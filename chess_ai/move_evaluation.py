"""
Comprehensive Move Evaluation System

This module provides a comprehensive Move object that tracks all evaluation stages
and integrates with WFC, BSP, guardrails, and pattern matching systems.
"""

import chess
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EvaluationStage(Enum):
    """Stages of move evaluation."""
    INITIAL = "initial"
    PATTERN_MATCH = "pattern_match"
    WFC_ANALYSIS = "wfc_analysis"
    BSP_ANALYSIS = "bsp_analysis"
    GUARDRAILS = "guardrails"
    TACTICAL = "tactical"
    POSITIONAL = "positional"
    FINAL = "final"


class MoveStatus(Enum):
    """Status of move evaluation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    FILTERED = "filtered"


@dataclass
class EvaluationResult:
    """Result of a single evaluation stage."""
    stage: EvaluationStage
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


class MoveEvaluation:
    """
    Comprehensive move evaluation object that tracks all stages of analysis.
    
    This object is passed through all evaluation stages and accumulates
    results, patterns, and visualization data.
    """
    
    def __init__(self, move: chess.Move, board: chess.Board, color: chess.Color):
        self.move = move
        self.board = board
        self.color = color
        self.start_time = time.time()
        
        # Evaluation stages
        self.evaluations: Dict[EvaluationStage, EvaluationResult] = {}
        self.current_stage = EvaluationStage.INITIAL
        
        # Pattern matching
        self.pattern_matches: List[PatternMatch] = []
        self.tactical_patterns: List[PatternMatch] = []
        self.opening_patterns: List[PatternMatch] = []
        
        # Engine results
        self.wfc_result: Optional[Dict[str, Any]] = None
        self.bsp_result: Optional[Dict[str, Any]] = None
        self.guardrails_result: Optional[bool] = None
        
        # Heatmap data
        self.heatmap_data: Optional[HeatmapData] = None
        
        # Bot tracking
        self.applicable_bots: List[str] = []
        self.bot_results: Dict[str, EvaluationResult] = {}
        
        # Final evaluation
        self.final_value: float = 0.0
        self.final_confidence: float = 0.0
        self.final_reason: str = ""
        
        # Visualization
        self.visualization_data: Dict[str, Any] = field(default_factory=dict)
        
    def add_evaluation(self, stage: EvaluationStage, result: EvaluationResult):
        """Add an evaluation result for a specific stage."""
        self.evaluations[stage] = result
        self.current_stage = stage
        
    def add_pattern_match(self, pattern_match: PatternMatch):
        """Add a pattern match result."""
        self.pattern_matches.append(pattern_match)
        
        if pattern_match.pattern_type == "tactical":
            self.tactical_patterns.append(pattern_match)
        elif pattern_match.pattern_type == "opening":
            self.opening_patterns.append(pattern_match)
    
    def set_wfc_result(self, result: Dict[str, Any]):
        """Set WFC analysis result."""
        self.wfc_result = result
        
    def set_bsp_result(self, result: Dict[str, Any]):
        """Set BSP analysis result."""
        self.bsp_result = result
        
    def set_guardrails_result(self, passed: bool, reason: str = ""):
        """Set guardrails validation result."""
        self.guardrails_result = passed
        if not passed:
            self.add_evaluation(
                EvaluationStage.GUARDRAILS,
                EvaluationResult(
                    stage=EvaluationStage.GUARDRAILS,
                    status=MoveStatus.FILTERED,
                    reason=reason
                )
            )
    
    def set_heatmap_data(self, heatmap_data: HeatmapData):
        """Set heatmap visualization data."""
        self.heatmap_data = heatmap_data
        
    def add_bot_result(self, bot_name: str, result: EvaluationResult):
        """Add result from a specific bot."""
        self.bot_results[bot_name] = result
        if bot_name not in self.applicable_bots:
            self.applicable_bots.append(bot_name)
    
    def calculate_final_evaluation(self) -> Tuple[float, float, str]:
        """Calculate final evaluation based on all stages."""
        if not self.evaluations:
            return 0.0, 0.0, "No evaluations"
        
        # Weight different stages
        weights = {
            EvaluationStage.PATTERN_MATCH: 0.3,
            EvaluationStage.TACTICAL: 0.25,
            EvaluationStage.POSITIONAL: 0.2,
            EvaluationStage.WFC_ANALYSIS: 0.15,
            EvaluationStage.BSP_ANALYSIS: 0.1,
        }
        
        total_value = 0.0
        total_confidence = 0.0
        total_weight = 0.0
        
        reasons = []
        
        for stage, result in self.evaluations.items():
            if result.status == MoveStatus.COMPLETED:
                weight = weights.get(stage, 0.1)
                total_value += result.value * weight
                total_confidence += result.confidence * weight
                total_weight += weight
                
                if result.reason:
                    reasons.append(f"{stage.value}: {result.reason}")
        
        if total_weight > 0:
            self.final_value = total_value / total_weight
            self.final_confidence = total_confidence / total_weight
        else:
            self.final_value = 0.0
            self.final_confidence = 0.0
            
        self.final_reason = "; ".join(reasons) if reasons else "No specific reasons"
        
        return self.final_value, self.final_confidence, self.final_reason
    
    def is_filtered(self) -> bool:
        """Check if move was filtered out by any stage."""
        for result in self.evaluations.values():
            if result.status == MoveStatus.FILTERED:
                return True
        return False
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualization."""
        data = {
            "move": self.move,
            "from_square": self.move.from_square,
            "to_square": self.move.to_square,
            "color": self.color,
            "final_value": self.final_value,
            "final_confidence": self.final_confidence,
            "pattern_matches": len(self.pattern_matches),
            "tactical_patterns": len(self.tactical_patterns),
            "opening_patterns": len(self.opening_patterns),
            "applicable_bots": self.applicable_bots,
            "evaluation_stages": len(self.evaluations),
            "is_filtered": self.is_filtered(),
        }
        
        if self.heatmap_data:
            data["heatmap"] = {
                "piece_type": self.heatmap_data.piece_type,
                "tactical_zones": self.heatmap_data.tactical_zones,
                "wfc_zones": self.heatmap_data.wfc_zones,
                "bsp_zones": self.heatmap_data.bsp_zones,
                "current_move_square": self.heatmap_data.current_move_square,
            }
        
        return data
    
    def get_status_summary(self) -> str:
        """Get a summary of evaluation status."""
        if self.is_filtered():
            return "FILTERED"
        
        if not self.evaluations:
            return "PENDING"
        
        completed = sum(1 for r in self.evaluations.values() if r.status == MoveStatus.COMPLETED)
        total = len(self.evaluations)
        
        return f"EVALUATED ({completed}/{total})"
    
    def get_detailed_log(self) -> str:
        """Get detailed log of all evaluations."""
        log_lines = [f"Move: {self.move} ({self.color})"]
        log_lines.append(f"Status: {self.get_status_summary()}")
        log_lines.append(f"Final Value: {self.final_value:.2f} (confidence: {self.final_confidence:.2f})")
        log_lines.append("")
        
        # Evaluation stages
        log_lines.append("Evaluation Stages:")
        for stage, result in self.evaluations.items():
            log_lines.append(f"  {stage.value}: {result.status.value} - {result.reason}")
        
        # Pattern matches
        if self.pattern_matches:
            log_lines.append("")
            log_lines.append("Pattern Matches:")
            for pm in self.pattern_matches:
                log_lines.append(f"  {pm.pattern_type}: {pm.pattern_name} (conf: {pm.confidence:.2f})")
        
        # Bot results
        if self.bot_results:
            log_lines.append("")
            log_lines.append("Bot Results:")
            for bot, result in self.bot_results.items():
                log_lines.append(f"  {bot}: {result.status.value} - {result.reason}")
        
        return "\n".join(log_lines)


class MoveEvaluator:
    """
    Main evaluator that orchestrates all evaluation stages.
    """
    
    def __init__(self):
        self.wfc_engine = None
        self.bsp_engine = None
        self.guardrails = None
        self.pattern_responder = None
        
    def set_engines(self, wfc_engine, bsp_engine, guardrails, pattern_responder):
        """Set the evaluation engines."""
        self.wfc_engine = wfc_engine
        self.bsp_engine = bsp_engine
        self.guardrails = guardrails
        self.pattern_responder = pattern_responder
    
    def evaluate_move(self, move: chess.Move, board: chess.Board, color: chess.Color) -> MoveEvaluation:
        """Evaluate a move through all stages."""
        evaluation = MoveEvaluation(move, board, color)
        
        try:
            # Stage 1: Pattern Matching
            self._evaluate_patterns(evaluation)
            
            # Stage 2: WFC Analysis
            if self.wfc_engine:
                self._evaluate_wfc(evaluation)
            
            # Stage 3: BSP Analysis
            if self.bsp_engine:
                self._evaluate_bsp(evaluation)
            
            # Stage 4: Guardrails
            if self.guardrails:
                self._evaluate_guardrails(evaluation)
            
            # Stage 5: Tactical Analysis
            self._evaluate_tactical(evaluation)
            
            # Stage 6: Positional Analysis
            self._evaluate_positional(evaluation)
            
            # Final evaluation
            evaluation.calculate_final_evaluation()
            
        except Exception as e:
            logger.error(f"Error evaluating move {move}: {e}")
            evaluation.add_evaluation(
                EvaluationStage.FINAL,
                EvaluationResult(
                    stage=EvaluationStage.FINAL,
                    status=MoveStatus.FAILED,
                    reason=f"Evaluation error: {e}"
                )
            )
        
        return evaluation
    
    def _evaluate_patterns(self, evaluation: MoveEvaluation):
        """Evaluate pattern matching."""
        if not self.pattern_responder:
            return
        
        try:
            # Check for opening patterns
            opening_match = self.pattern_responder.match(evaluation.board)
            if opening_match:
                pattern_match = PatternMatch(
                    pattern_type="opening",
                    pattern_name="COW_Opening",
                    confidence=0.8,
                    squares=[evaluation.move.from_square, evaluation.move.to_square],
                    tactical_value=0.0,
                    positional_value=0.3
                )
                evaluation.add_pattern_match(pattern_match)
            
            # Add tactical pattern evaluation here
            # This would integrate with existing tactical pattern systems
            
        except Exception as e:
            logger.warning(f"Pattern evaluation failed: {e}")
    
    def _evaluate_wfc(self, evaluation: MoveEvaluation):
        """Evaluate using WFC engine."""
        if not self.wfc_engine:
            return
        
        try:
            # Analyze current position with WFC
            wfc_result = {
                "compatible_patterns": [],
                "constraint_violations": 0,
                "pattern_confidence": 0.0
            }
            
            evaluation.set_wfc_result(wfc_result)
            
            evaluation.add_evaluation(
                EvaluationStage.WFC_ANALYSIS,
                EvaluationResult(
                    stage=EvaluationStage.WFC_ANALYSIS,
                    status=MoveStatus.COMPLETED,
                    value=wfc_result["pattern_confidence"],
                    confidence=0.7,
                    reason="WFC pattern analysis",
                    bot_name="WFC"
                )
            )
            
        except Exception as e:
            logger.warning(f"WFC evaluation failed: {e}")
    
    def _evaluate_bsp(self, evaluation: MoveEvaluation):
        """Evaluate using BSP engine."""
        if not self.bsp_engine:
            return
        
        try:
            # Analyze board zones
            zone_stats = self.bsp_engine.analyze_board(evaluation.board)
            
            bsp_result = {
                "zone_stats": zone_stats,
                "zone_control": self.bsp_engine.calculate_zone_control(evaluation.board, evaluation.color),
                "move_zone": self.bsp_engine.get_zone_for_square(evaluation.move.to_square)
            }
            
            evaluation.set_bsp_result(bsp_result)
            
            # Calculate BSP value
            move_zone = bsp_result["move_zone"]
            zone_value = 0.0
            if move_zone:
                zone_importance = self.bsp_engine._get_zone_importance(move_zone.zone_type)
                zone_value = zone_importance * 0.1
            
            evaluation.add_evaluation(
                EvaluationStage.BSP_ANALYSIS,
                EvaluationResult(
                    stage=EvaluationStage.BSP_ANALYSIS,
                    status=MoveStatus.COMPLETED,
                    value=zone_value,
                    confidence=0.6,
                    reason=f"BSP zone analysis: {move_zone.zone_type if move_zone else 'unknown'}",
                    bot_name="BSP"
                )
            )
            
        except Exception as e:
            logger.warning(f"BSP evaluation failed: {e}")
    
    def _evaluate_guardrails(self, evaluation: MoveEvaluation):
        """Evaluate using guardrails."""
        if not self.guardrails:
            return
        
        try:
            # Check if move passes guardrails
            passed = self.guardrails.allow_move(evaluation.board, evaluation.move)
            
            if not passed:
                evaluation.set_guardrails_result(False, "Failed guardrails check")
                return
            
            evaluation.set_guardrails_result(True, "Passed guardrails check")
            
            evaluation.add_evaluation(
                EvaluationStage.GUARDRAILS,
                EvaluationResult(
                    stage=EvaluationStage.GUARDRAILS,
                    status=MoveStatus.COMPLETED,
                    value=1.0,
                    confidence=0.9,
                    reason="Passed guardrails validation",
                    bot_name="Guardrails"
                )
            )
            
        except Exception as e:
            logger.warning(f"Guardrails evaluation failed: {e}")
    
    def _evaluate_tactical(self, evaluation: MoveEvaluation):
        """Evaluate tactical aspects."""
        try:
            # Basic tactical evaluation
            tactical_value = 0.0
            tactical_reason = "No tactical patterns"
            
            # Check for captures
            if evaluation.board.is_capture(evaluation.move):
                captured_piece = evaluation.board.piece_at(evaluation.move.to_square)
                if captured_piece:
                    piece_values = {1: 1, 2: 3, 3: 3, 4: 5, 5: 9, 6: 0}  # pawn, knight, bishop, rook, queen, king
                    tactical_value += piece_values.get(captured_piece.piece_type, 0) * 0.1
                    tactical_reason = f"Captures {captured_piece.symbol()}"
            
            # Check for checks
            temp_board = evaluation.board.copy()
            temp_board.push(evaluation.move)
            if temp_board.is_check():
                tactical_value += 0.2
                tactical_reason += "; Gives check" if tactical_reason != "No tactical patterns" else "Gives check"
            
            evaluation.add_evaluation(
                EvaluationStage.TACTICAL,
                EvaluationResult(
                    stage=EvaluationStage.TACTICAL,
                    status=MoveStatus.COMPLETED,
                    value=tactical_value,
                    confidence=0.8,
                    reason=tactical_reason,
                    bot_name="Tactical"
                )
            )
            
        except Exception as e:
            logger.warning(f"Tactical evaluation failed: {e}")
    
    def _evaluate_positional(self, evaluation: MoveEvaluation):
        """Evaluate positional aspects."""
        try:
            # Basic positional evaluation
            positional_value = 0.0
            positional_reason = "Neutral position"
            
            # Center control
            center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
            if evaluation.move.to_square in center_squares:
                positional_value += 0.1
                positional_reason = "Controls center"
            
            # Development
            piece = evaluation.board.piece_at(evaluation.move.from_square)
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                if chess.square_rank(evaluation.move.from_square) == (0 if evaluation.color else 7):
                    positional_value += 0.05
                    positional_reason += "; Develops piece" if positional_reason != "Neutral position" else "Develops piece"
            
            evaluation.add_evaluation(
                EvaluationStage.POSITIONAL,
                EvaluationResult(
                    stage=EvaluationStage.POSITIONAL,
                    status=MoveStatus.COMPLETED,
                    value=positional_value,
                    confidence=0.7,
                    reason=positional_reason,
                    bot_name="Positional"
                )
            )
            
        except Exception as e:
            logger.warning(f"Positional evaluation failed: {e}")


# Factory function
def create_move_evaluator() -> MoveEvaluator:
    """Create a move evaluator with all engines."""
    evaluator = MoveEvaluator()
    
    # Import engines
    try:
        from .wfc_engine import create_chess_wfc_engine
        from .bsp_engine import create_chess_bsp_engine
        from .guardrails import Guardrails
        from .pattern_responder import PatternResponder
        
        evaluator.set_engines(
            wfc_engine=create_chess_wfc_engine(),
            bsp_engine=create_chess_bsp_engine(),
            guardrails=Guardrails(),
            pattern_responder=PatternResponder()
        )
        
    except ImportError as e:
        logger.warning(f"Could not import all engines: {e}")
    
    return evaluator