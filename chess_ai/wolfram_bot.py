"""WolframBot - Chess agent using Wolfram Engine for position evaluation.

This bot leverages the Wolfram Engine to perform advanced mathematical
analysis of chess positions, including pattern recognition, tactical
evaluation, and strategic assessment.
"""

import logging
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import chess
import chess.engine

from .bot_agent import BotAgent

logger = logging.getLogger(__name__)


class WolframBot(BotAgent):
    """Chess bot that uses Wolfram Engine for position evaluation.
    
    This bot can perform various types of analysis using Wolfram's
    computational capabilities:
    - Pattern recognition and matching
    - Mathematical evaluation of piece relationships
    - Tactical sequence analysis
    - Strategic position assessment
    """
    
    def __init__(
        self,
        color: chess.Color,
        wolfram_script_path: Optional[str] = None,
        evaluation_depth: int = 3,
        use_pattern_analysis: bool = True,
        use_tactical_analysis: bool = True,
        use_strategic_analysis: bool = True,
        confidence_threshold: float = 0.6
    ):
        """Initialize WolframBot.
        
        Args:
            color: Chess color (WHITE or BLACK)
            wolfram_script_path: Path to Wolfram evaluation script
            evaluation_depth: Depth of analysis (1-5)
            use_pattern_analysis: Enable pattern recognition
            use_tactical_analysis: Enable tactical analysis
            use_strategic_analysis: Enable strategic analysis
            confidence_threshold: Minimum confidence for move selection
        """
        super().__init__(color)
        
        self.wolfram_script_path = wolfram_script_path or self._find_wolfram_script()
        self.evaluation_depth = max(1, min(5, evaluation_depth))
        self.use_pattern_analysis = use_pattern_analysis
        self.use_tactical_analysis = use_tactical_analysis
        self.use_strategic_analysis = use_strategic_analysis
        self.confidence_threshold = confidence_threshold
        
        # Verify Wolfram Engine is available
        self._verify_wolfram_engine()
        
        logger.info(f"WolframBot initialized with depth={evaluation_depth}")
    
    def _find_wolfram_script(self) -> str:
        """Find the Wolfram evaluation script."""
        script_path = Path(__file__).parent / "wolfram_evaluation.wl"
        if script_path.exists():
            return str(script_path)
        
        # Fallback to analysis directory
        analysis_script = Path(__file__).parent.parent / "analysis" / "wolfram_evaluation.wl"
        if analysis_script.exists():
            return str(analysis_script)
        
        raise FileNotFoundError("Wolfram evaluation script not found")
    
    def _verify_wolfram_engine(self) -> None:
        """Verify that Wolfram Engine is available."""
        try:
            result = subprocess.run(
                ["wolframscript", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError("Wolfram Engine not properly installed")
            logger.info("Wolfram Engine verified successfully")
        except FileNotFoundError:
            raise RuntimeError(
                "Wolfram Engine not found. Please install from https://www.wolfram.com/engine/"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Wolfram Engine verification timed out")
    
    def choose_move(self, board: chess.Board, debug: bool = False) -> Tuple[chess.Move, float]:
        """Choose the best move using Wolfram Engine analysis.
        
        Args:
            board: Current chess position
            debug: Enable debug output
            
        Returns:
            Tuple of (best_move, confidence_score)
        """
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available")
        
        if len(legal_moves) == 1:
            return legal_moves[0], 1.0
        
        # Generate move evaluations using Wolfram Engine
        move_evaluations = self._evaluate_moves_with_wolfram(board, legal_moves, debug)
        
        if not move_evaluations:
            # Fallback to intelligent move selection if Wolfram analysis fails
            logger.warning("Wolfram analysis failed, using intelligent fallback")
            return self._intelligent_fallback(board, legal_moves)
        
        # Select best move based on evaluation
        best_move = max(move_evaluations, key=lambda x: x[1])
        confidence = min(1.0, max(0.0, best_move[1]))
        
        if debug:
            logger.info(f"WolframBot selected {best_move[0]} with confidence {confidence:.3f}")
            logger.info(f"Evaluated {len(move_evaluations)} moves")
        
        return best_move[0], confidence
    
    def _evaluate_moves_with_wolfram(
        self, 
        board: chess.Board, 
        moves: List[chess.Move], 
        debug: bool = False
    ) -> List[Tuple[chess.Move, float]]:
        """Evaluate moves using Wolfram Engine.
        
        Args:
            board: Current position
            moves: List of legal moves to evaluate
            debug: Enable debug output
            
        Returns:
            List of (move, score) tuples
        """
        try:
            # Create temporary file for position data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                position_data = {
                    "fen": board.fen(),
                    "moves": [move.uci() for move in moves],
                    "depth": self.evaluation_depth,
                    "analysis_types": {
                        "pattern": self.use_pattern_analysis,
                        "tactical": self.use_tactical_analysis,
                        "strategic": self.use_strategic_analysis
                    }
                }
                json.dump(position_data, f)
                temp_file = f.name
            
            # Run Wolfram evaluation
            cmd = [
                "wolframscript",
                "-file", self.wolfram_script_path,
                temp_file
            ]
            
            if debug:
                logger.info(f"Running Wolfram command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Wolfram script failed: {result.stderr}")
                return []
            
            # Parse results
            evaluations = json.loads(result.stdout)
            
            # Convert to move objects and scores
            move_scores = []
            for move_uci, score in evaluations.items():
                try:
                    move = chess.Move.from_uci(move_uci)
                    if move in moves:
                        move_scores.append((move, float(score)))
                except ValueError:
                    logger.warning(f"Invalid move UCI: {move_uci}")
                    continue
            
            return move_scores
            
        except subprocess.TimeoutExpired:
            logger.error("Wolfram evaluation timed out")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Wolfram output: {e}")
            return []
        except Exception as e:
            logger.error(f"Wolfram evaluation failed: {e}")
            return []
        finally:
            # Clean up temporary file
            try:
                Path(temp_file).unlink()
            except:
                pass
    
    def get_position_evaluation(self, board: chess.Board) -> Dict[str, Any]:
        """Get detailed position evaluation using Wolfram Engine.
        
        Args:
            board: Chess position to evaluate
            
        Returns:
            Dictionary containing evaluation details
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                position_data = {
                    "fen": board.fen(),
                    "analysis_types": {
                        "pattern": self.use_pattern_analysis,
                        "tactical": self.use_tactical_analysis,
                        "strategic": self.use_strategic_analysis
                    }
                }
                json.dump(position_data, f)
                temp_file = f.name
            
            cmd = [
                "wolframscript",
                "-file", self.wolfram_script_path,
                "--position-analysis",
                temp_file
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Position analysis failed: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Position evaluation failed: {e}")
            return {}
        finally:
            try:
                Path(temp_file).unlink()
            except:
                pass
    
    def __str__(self) -> str:
        return f"WolframBot(depth={self.evaluation_depth})"
    
    def __repr__(self) -> str:
        return (f"WolframBot(color={self.color}, depth={self.evaluation_depth}, "
                f"pattern={self.use_pattern_analysis}, tactical={self.use_tactical_analysis}, "
                f"strategic={self.use_strategic_analysis})")