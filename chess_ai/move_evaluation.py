"""
Comprehensive Move Evaluation System

This module provides a comprehensive Move object that tracks all evaluation stages
and integrates with WFC, BSP, guardrails, and pattern matching systems.

Updated to use the unified MoveObject from core.move_object.
"""

import chess
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import the unified move object
from core.move_object import (
    MoveObject, MovePhase, MoveStatus, MethodStatus, 
    EvaluationStep, MethodResult, VisualizationState,
    create_move_object, move_evaluation_manager
)

logger = logging.getLogger(__name__)


# Backward compatibility aliases
EvaluationStage = MovePhase  # Map old enum to new one
MoveEvaluation = MoveObject  # Use unified MoveObject


@dataclass
class EvaluationResult:
    """Result of a single evaluation stage."""
    stage: MovePhase
    status: MoveStatus
    value: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    bot_name: str = ""


@dataclass
class PatternMatch:
    """Pattern matching result."""
    pattern_type: str
    pattern_name: str
    confidence: float
    squares: List[chess.Square]
    tactical_value: float = 0.0
    positional_value: float = 0.0


@dataclass
class HeatmapData:
    """Heatmap visualization data."""
    piece_type: str
    heatmap_values: List[List[float]]
    tactical_zones: List[chess.Square] = field(default_factory=list)
    wfc_zones: List[chess.Square] = field(default_factory=list)
    bsp_zones: List[chess.Square] = field(default_factory=list)
    current_move_square: Optional[chess.Square] = None


class MoveEvaluator:
    """
    Comprehensive move evaluator that integrates multiple evaluation methods.
    
    This class provides a high-level interface for evaluating chess moves
    using pattern matching, WFC, BSP, guardrails, and other methods.
    """
    
    def __init__(self):
        self.pattern_responder = None
        self.wfc_engine = None
        self.bsp_engine = None
        self.guardrails = None
        
        # Initialize engines (these would be imported from their respective modules)
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize evaluation engines."""
        try:
            from core.pattern_loader import PatternResponder
            self.pattern_responder = PatternResponder()
            logger.info("✓ PatternResponder initialized")
        except ImportError as e:
            logger.warning(f"PatternResponder not available: {e}")
        
        try:
            from chess_ai.wfc_engine import create_chess_wfc_engine
            self.wfc_engine = create_chess_wfc_engine()
            logger.info("✓ WFC Engine initialized")
        except ImportError as e:
            logger.warning(f"WFC Engine not available: {e}")
        
        try:
            from chess_ai.bsp_engine import create_chess_bsp_engine
            self.bsp_engine = create_chess_bsp_engine()
            logger.info("✓ BSP Engine initialized")
        except ImportError as e:
            logger.warning(f"BSP Engine not available: {e}")
        
        try:
            from chess_ai.guardrails import Guardrails
            self.guardrails = Guardrails()
            logger.info("✓ Guardrails initialized")
        except ImportError as e:
            logger.warning(f"Guardrails not available: {e}")
    
    def evaluate_move(self, move: chess.Move, board: chess.Board, color: chess.Color) -> MoveObject:
        """Evaluate a move through all stages."""
        # Create move evaluation using the unified move object
        evaluation = create_move_object(move, board, f"MoveEvaluator_{color}")
        
        try:
            # Stage 1: Pattern Matching
            self._evaluate_patterns(evaluation)
            
            # Stage 2: WFC Analysis
            self._evaluate_wfc(evaluation)
            
            # Stage 3: BSP Analysis
            self._evaluate_bsp(evaluation)
            
            # Stage 4: Guardrails
            self._evaluate_guardrails(evaluation)
            
            # Stage 5: Tactical Evaluation
            self._evaluate_tactical(evaluation)
            
            # Stage 6: Positional Evaluation
            self._evaluate_positional(evaluation)
            
            # Finalize evaluation
            evaluation.finalize_evaluation(
                final_score=evaluation.final_score,
                reason=evaluation.primary_reason,
                confidence=evaluation.confidence
            )
            
        except Exception as e:
            logger.error(f"Error evaluating move {move}: {e}")
            evaluation.set_error(str(e))
        
        return evaluation
    
    def _evaluate_patterns(self, evaluation: MoveObject):
        """Evaluate pattern matching."""
        if not self.pattern_responder:
            evaluation.add_method_result(
                "PatternResponder",
                MethodStatus.SKIPPED,
                reason="PatternResponder not available"
            )
            return
        
        try:
            evaluation.start_phase(MovePhase.PATTERN_MATCHING)
            
            # Get pattern matches
            patterns = self.pattern_responder.find_patterns(evaluation.board_fen)
            
            pattern_score = 0.0
            for pattern in patterns:
                evaluation.add_pattern_match(
                    pattern_type=pattern.get('type', 'unknown'),
                    pattern_data=pattern,
                    confidence=pattern.get('confidence', 0.0)
                )
                pattern_score += pattern.get('value', 0.0)
            
            evaluation.pattern_score = pattern_score
            
            evaluation.add_method_result(
                "PatternResponder",
                MethodStatus.COMPLETED,
                value=pattern_score,
                active=True,
                confidence=min(pattern_score / 100.0, 1.0),
                reason=f"Found {len(patterns)} patterns"
            )
            
        except Exception as e:
            evaluation.add_method_result(
                "PatternResponder",
                MethodStatus.FAILED,
                reason=f"Pattern evaluation failed: {e}"
            )
        finally:
            evaluation.end_phase(MovePhase.PATTERN_MATCHING)
    
    def _evaluate_wfc(self, evaluation: MoveObject):
        """Evaluate using WFC engine."""
        if not self.wfc_engine:
            evaluation.add_method_result(
                "WFCEngine",
                MethodStatus.SKIPPED,
                reason="WFC Engine not available"
            )
            return
        
        try:
            evaluation.start_phase(MovePhase.WFC_ANALYSIS)
            
            # Analyze with WFC
            wfc_result = self.wfc_engine.analyze_position(evaluation.board_fen)
            wfc_score = wfc_result.get('score', 0.0)
            
            evaluation.wfc_score = wfc_score
            evaluation.set_wfc_analysis(wfc_result)
            
            evaluation.add_method_result(
                "WFCEngine",
                MethodStatus.COMPLETED,
                value=wfc_score,
                active=True,
                confidence=min(wfc_score / 100.0, 1.0),
                reason=f"WFC analysis score: {wfc_score:.2f}"
            )
            
        except Exception as e:
            evaluation.add_method_result(
                "WFCEngine",
                MethodStatus.FAILED,
                reason=f"WFC evaluation failed: {e}"
            )
        finally:
            evaluation.end_phase(MovePhase.WFC_ANALYSIS)
    
    def _evaluate_bsp(self, evaluation: MoveObject):
        """Evaluate using BSP engine."""
        if not self.bsp_engine:
            evaluation.add_method_result(
                "BSPEngine",
                MethodStatus.SKIPPED,
                reason="BSP Engine not available"
            )
            return
        
        try:
            evaluation.start_phase(MovePhase.BSP_ANALYSIS)
            
            # Analyze with BSP
            bsp_result = self.bsp_engine.analyze_position(evaluation.board_fen)
            bsp_score = bsp_result.get('score', 0.0)
            
            evaluation.bsp_score = bsp_score
            evaluation.set_bsp_analysis(bsp_result)
            
            evaluation.add_method_result(
                "BSPEngine",
                MethodStatus.COMPLETED,
                value=bsp_score,
                active=True,
                confidence=min(bsp_score / 100.0, 1.0),
                reason=f"BSP analysis score: {bsp_score:.2f}"
            )
            
        except Exception as e:
            evaluation.add_method_result(
                "BSPEngine",
                MethodStatus.FAILED,
                reason=f"BSP evaluation failed: {e}"
            )
        finally:
            evaluation.end_phase(MovePhase.BSP_ANALYSIS)
    
    def _evaluate_guardrails(self, evaluation: MoveObject):
        """Evaluate using guardrails."""
        if not self.guardrails:
            evaluation.add_method_result(
                "Guardrails",
                MethodStatus.SKIPPED,
                reason="Guardrails not available"
            )
            return
        
        try:
            evaluation.start_phase(MovePhase.GUARDRAILS_CHECK)
            
            # Check guardrails
            board = chess.Board(evaluation.board_fen)
            allow_move, violations = self.guardrails.check_move(board, evaluation.move)
            
            if not allow_move:
                for violation in violations:
                    evaluation.add_guardrails_violation(violation)
            
            evaluation.add_method_result(
                "Guardrails",
                MethodStatus.COMPLETED,
                value=1.0 if allow_move else 0.0,
                active=True,
                confidence=1.0,
                reason=f"Guardrails: {'PASS' if allow_move else 'FAIL'}"
            )
            
        except Exception as e:
            evaluation.add_method_result(
                "Guardrails",
                MethodStatus.FAILED,
                reason=f"Guardrails evaluation failed: {e}"
            )
        finally:
            evaluation.end_phase(MovePhase.GUARDRAILS_CHECK)
    
    def _evaluate_tactical(self, evaluation: MoveObject):
        """Evaluate tactical aspects."""
        try:
            evaluation.start_phase(MovePhase.TACTICAL_EVALUATION)
            
            # Basic tactical evaluation
            board = chess.Board(evaluation.board_fen)
            
            # Check for basic tactical motifs
            tactical_score = 0.0
            motifs = []
            
            # Check for captures
            if board.is_capture(evaluation.move):
                tactical_score += 50.0
                motifs.append("capture")
            
            # Check for checks
            temp_board = board.copy()
            temp_board.push(evaluation.move)
            if temp_board.is_check():
                tactical_score += 30.0
                motifs.append("check")
            
            # Check for threats
            # (This would be expanded with more sophisticated tactical analysis)
            
            evaluation.tactical_score = tactical_score
            evaluation.tactical_motifs = motifs
            
            evaluation.add_method_result(
                "TacticalAnalyzer",
                MethodStatus.COMPLETED,
                value=tactical_score,
                active=True,
                confidence=min(tactical_score / 100.0, 1.0),
                reason=f"Tactical motifs: {', '.join(motifs) if motifs else 'none'}"
            )
            
        except Exception as e:
            evaluation.add_method_result(
                "TacticalAnalyzer",
                MethodStatus.FAILED,
                reason=f"Tactical evaluation failed: {e}"
            )
        finally:
            evaluation.end_phase(MovePhase.TACTICAL_EVALUATION)
    
    def _evaluate_positional(self, evaluation: MoveObject):
        """Evaluate positional aspects."""
        try:
            evaluation.start_phase(MovePhase.BOT_EVALUATION)  # Using BOT_EVALUATION for positional
            
            # Basic positional evaluation
            board = chess.Board(evaluation.board_fen)
            
            # Simple positional scoring
            positional_score = 0.0
            
            # Center control
            center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
            for square in center_squares:
                if board.piece_at(square) and board.piece_at(square).color == evaluation.color:
                    positional_score += 10.0
            
            # Development
            piece_count = len([p for p in board.piece_map().values() if p.color == evaluation.color])
            positional_score += piece_count * 5.0
            
            evaluation.positional_score = positional_score
            
            evaluation.add_method_result(
                "PositionalAnalyzer",
                MethodStatus.COMPLETED,
                value=positional_score,
                active=True,
                confidence=min(positional_score / 100.0, 1.0),
                reason=f"Positional score: {positional_score:.2f}"
            )
            
        except Exception as e:
            evaluation.add_method_result(
                "PositionalAnalyzer",
                MethodStatus.FAILED,
                reason=f"Positional evaluation failed: {e}"
            )
        finally:
            evaluation.end_phase(MovePhase.BOT_EVALUATION)
    
    def get_evaluation_summary(self, evaluation: MoveObject) -> Dict[str, Any]:
        """Get a summary of the evaluation."""
        return evaluation.get_evaluation_summary()


def create_move_evaluator() -> MoveEvaluator:
    """Factory function to create a MoveEvaluator instance."""
    return MoveEvaluator()


# Backward compatibility functions
def create_move_evaluation(move: chess.Move, board: chess.Board, color: chess.Color) -> MoveObject:
    """Create a move evaluation (backward compatibility)."""
    return create_move_object(move, board, f"MoveEvaluator_{color}")


# Export the main classes and functions
__all__ = [
    'MoveObject', 'MovePhase', 'MoveStatus', 'MethodStatus',
    'EvaluationStep', 'MethodResult', 'VisualizationState',
    'MoveEvaluator', 'create_move_evaluator', 'create_move_evaluation',
    'PatternMatch', 'HeatmapData', 'EvaluationResult',
    # Backward compatibility
    'MoveEvaluation', 'EvaluationStage'
]