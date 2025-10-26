"""
Comprehensive Move Object for Chess AI Evaluation Tracking.

This module provides a unified Move object that tracks all evaluation data throughout
the move selection pipeline, including bot decisions, pattern matching,
WFC/BSP analysis, method results, and visualization states.

Combines the best features from both implementations:
- Comprehensive evaluation pipeline tracking
- Method result tracking with status indicators
- Visualization state management
- Game-wide move evaluation management
- Performance statistics and analysis
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import chess
from chess import Move, Board, Square


class MovePhase(Enum):
    """Phases of move evaluation pipeline."""
    INITIALIZATION = "initialization"
    PATTERN_MATCHING = "pattern_matching"
    WFC_ANALYSIS = "wfc_analysis"
    BSP_ANALYSIS = "bsp_analysis"
    HEATMAP_EVALUATION = "heatmap_evaluation"
    TACTICAL_EVALUATION = "tactical_evaluation"
    BOT_EVALUATION = "bot_evaluation"
    GUARDRAILS_CHECK = "guardrails_check"
    MINIMAX_EVALUATION = "minimax_evaluation"
    FINAL_SELECTION = "final_selection"
    VISUALIZATION = "visualization"


class MoveStatus(Enum):
    """Status of move evaluation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"


class MethodStatus(Enum):
    """Status of method processing with visual indicators."""
    PENDING = "⏳ PENDING"
    PROCESSING = "⚙️ PROCESSING"
    COMPLETED = "✅ COMPLETED"
    SKIPPED = "⏭️ SKIPPED"
    FAILED = "❌ FAILED"


@dataclass
class EvaluationStep:
    """Represents a single evaluation step in the move pipeline."""
    method_name: str
    bot_name: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: MoveStatus = MoveStatus.PENDING
    confidence: float = 0.0
    reason: str = ""
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodResult:
    """Result from a single evaluation method with enhanced tracking."""
    method_name: str
    status: MethodStatus
    value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    active_in_board: bool = False  # Whether this method applies to current position
    timestamp: float = field(default_factory=time.time)
    processing_time_ms: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    
    def __str__(self) -> str:
        active_str = "🟢 ACTIVE" if self.active_in_board else ""
        value_str = f"={self.value:.2f}" if self.value is not None else ""
        return f"{self.status.value} {self.method_name}{value_str} {active_str}"


@dataclass
class VisualizationState:
    """Tracks visualization state for the move."""
    heatmap_piece: Optional[str] = None
    heatmap_set: Optional[str] = None
    heatmap_intensity: Optional[float] = None
    heatmap_cell_color: str = "red"  # red/blue/purple/green gradient
    highlighted_squares: Set[Square] = field(default_factory=set)
    zone_colors: Dict[str, str] = field(default_factory=dict)  # zone_type -> color
    current_cell: Optional[Square] = None  # For real-time visualization
    bsp_zones: List[Dict[str, Any]] = field(default_factory=list)
    wfc_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # BSP zone data
    bsp_zone_type: Optional[str] = None
    bsp_zone_control: Optional[float] = None
    bsp_zone_cells: List[Square] = field(default_factory=list)
    
    # WFC pattern data
    wfc_patterns_matched: List[str] = field(default_factory=list)
    wfc_constraints_satisfied: List[str] = field(default_factory=list)


@dataclass
class MoveObject:
    """
    Comprehensive move evaluation object that tracks all parameters and evaluations
    throughout the move pipeline.
    
    Combines features from both implementations:
    - Complete evaluation pipeline tracking
    - Method result tracking with visual status indicators
    - Heatmap and visualization state management
    - Tactical evaluation tracking
    - Guardrails and safety checks
    - Performance metrics and timing
    """
    
    # Basic move information
    move: Move
    board_fen: str
    move_number: int
    color: chess.Color
    san_notation: str = ""
    
    # Evaluation pipeline tracking
    current_phase: MovePhase = MovePhase.INITIALIZATION
    status: MoveStatus = MoveStatus.PENDING
    evaluation_steps: List[EvaluationStep] = field(default_factory=list)
    
    # Method results tracking (from second implementation)
    method_results: Dict[str, MethodResult] = field(default_factory=dict)
    
    # Timing information
    created_at: float = field(default_factory=time.time)
    total_duration_ms: float = 0.0
    phase_durations: Dict[MovePhase, float] = field(default_factory=dict)
    
    # Score components (from second implementation)
    base_score: float = 0.0
    pattern_score: float = 0.0
    wfc_score: float = 0.0
    bsp_score: float = 0.0
    heatmap_score: float = 0.0
    tactical_score: float = 0.0
    positional_score: float = 0.0
    minimax_score: float = 0.0
    final_score: float = 0.0
    
    # Evaluation results
    confidence: float = 0.0
    primary_reason: str = ""
    contributing_factors: Dict[str, float] = field(default_factory=dict)
    
    # Pattern and engine analysis
    pattern_matches: List[Dict[str, Any]] = field(default_factory=list)
    wfc_analysis: Dict[str, Any] = field(default_factory=dict)
    bsp_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Bot evaluations
    bot_evaluations: Dict[str, EvaluationStep] = field(default_factory=dict)
    
    # Tactical evaluation (from second implementation)
    tactical_motifs: List[str] = field(default_factory=list)  # fork, pin, skewer, etc.
    tactical_threats: List[str] = field(default_factory=list)
    
    # Guardrails and safety
    guardrails_passed: bool = True
    guardrails_violations: List[str] = field(default_factory=list)
    guardrails_warnings: List[str] = field(default_factory=list)
    
    # Minimax data (from second implementation)
    minimax_depth: int = 0
    minimax_value: Optional[float] = None
    minimax_pv: List[Move] = field(default_factory=list)  # Principal variation
    meets_minimax_threshold: bool = False  # value > 10% of neutral
    
    # Visualization state
    visualization: VisualizationState = field(default_factory=VisualizationState)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    bot_name: Optional[str] = None
    
    def add_evaluation_step(self, step: EvaluationStep) -> None:
        """Add an evaluation step to the pipeline."""
        step.timestamp = time.time()
        self.evaluation_steps.append(step)
        
        if step.bot_name:
            self.bot_evaluations[step.bot_name] = step
    
    def add_method_result(
        self,
        method_name: str,
        status: MethodStatus,
        value: Optional[float] = None,
        active: bool = False,
        confidence: float = 0.0,
        reason: str = "",
        **metadata
    ) -> None:
        """Add or update a method result."""
        result = MethodResult(
            method_name=method_name,
            status=status,
            value=value,
            metadata=metadata,
            active_in_board=active,
            confidence=confidence,
            reason=reason
        )
        self.method_results[method_name] = result
    
    def start_phase(self, phase: MovePhase) -> None:
        """Start a new evaluation phase."""
        self.current_phase = phase
        self.phase_durations[phase] = time.time()
    
    def end_phase(self, phase: MovePhase) -> None:
        """End the current evaluation phase."""
        if phase in self.phase_durations:
            duration = time.time() - self.phase_durations[phase]
            self.phase_durations[phase] = duration * 1000  # Convert to ms
    
    def add_pattern_match(self, pattern_type: str, pattern_data: Dict[str, Any], 
                         confidence: float = 1.0) -> None:
        """Add a pattern match result."""
        match = {
            'type': pattern_type,
            'data': pattern_data,
            'confidence': confidence,
            'timestamp': time.time()
        }
        self.pattern_matches.append(match)
    
    def set_wfc_analysis(self, analysis: Dict[str, Any]) -> None:
        """Set WFC analysis results."""
        self.wfc_analysis = analysis
        self.wfc_analysis['timestamp'] = time.time()
    
    def set_bsp_analysis(self, analysis: Dict[str, Any]) -> None:
        """Set BSP analysis results."""
        self.bsp_analysis = analysis
        self.bsp_analysis['timestamp'] = time.time()
    
    def add_guardrails_violation(self, violation: str) -> None:
        """Add a guardrails violation."""
        self.guardrails_violations.append(violation)
        self.guardrails_passed = False
    
    def add_guardrails_warning(self, warning: str) -> None:
        """Add a guardrails warning."""
        self.guardrails_warnings.append(warning)
    
    def update_visualization(self, **kwargs) -> None:
        """Update visualization state."""
        for key, value in kwargs.items():
            if hasattr(self.visualization, key):
                setattr(self.visualization, key, value)
    
    def get_active_bots(self) -> List[str]:
        """Get list of bots that evaluated this move."""
        return list(self.bot_evaluations.keys())
    
    def get_active_methods(self) -> List[MethodResult]:
        """Get all methods that are active for this position."""
        return [r for r in self.method_results.values() if r.active_in_board]
    
    def get_method_by_phase(self, phase: MovePhase) -> List[MethodResult]:
        """Get method results by evaluation phase."""
        phase_methods = {
            MovePhase.PATTERN_MATCHING: ['PatternResponder', 'OpeningBook'],
            MovePhase.WFC_ANALYSIS: ['WFCEngine'],
            MovePhase.BSP_ANALYSIS: ['BSPEngine'],
            MovePhase.HEATMAP_EVALUATION: ['HeatmapEval'],
            MovePhase.TACTICAL_EVALUATION: ['TacticalAnalyzer', 'ThreatGuard'],
            MovePhase.GUARDRAILS_CHECK: ['Guardrails'],
            MovePhase.MINIMAX_EVALUATION: ['Minimax', 'AlphaBeta'],
        }
        
        method_names = phase_methods.get(phase, [])
        return [self.method_results[name] for name in method_names if name in self.method_results]
    
    def calculate_final_score(self) -> float:
        """Calculate the final weighted score from all components."""
        # Weight different components
        weights = {
            'pattern': 0.15,
            'wfc': 0.10,
            'bsp': 0.10,
            'heatmap': 0.15,
            'tactical': 0.20,
            'positional': 0.10,
            'minimax': 0.20
        }
        
        self.final_score = (
            weights['pattern'] * self.pattern_score +
            weights['wfc'] * self.wfc_score +
            weights['bsp'] * self.bsp_score +
            weights['heatmap'] * self.heatmap_score +
            weights['tactical'] * self.tactical_score +
            weights['positional'] * self.positional_score +
            weights['minimax'] * self.minimax_score
        )
        
        # Apply guardrails penalty
        if not self.guardrails_passed:
            self.final_score *= 0.5
        
        return self.final_score
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get a summary of the evaluation process."""
        return {
            'move': self.san_notation or str(self.move),
            'phase': self.current_phase.value,
            'status': self.status.value,
            'total_duration_ms': self.total_duration_ms,
            'final_score': self.final_score,
            'confidence': self.confidence,
            'primary_reason': self.primary_reason,
            'active_bots': self.get_active_bots(),
            'pattern_matches': len(self.pattern_matches),
            'guardrails_passed': self.guardrails_passed,
            'violations': len(self.guardrails_violations),
            'tactical_motifs': self.tactical_motifs,
            'minimax_threshold_met': self.meets_minimax_threshold
        }
    
    def get_timing_breakdown(self) -> Dict[str, float]:
        """Get timing breakdown by phase."""
        return {phase.value: duration for phase, duration in self.phase_durations.items()}
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualization in the UI."""
        return {
            'move': self.move.uci(),
            'from_square': self.move.from_square,
            'to_square': self.move.to_square,
            'phase': self.current_phase.value,
            'final_score': self.final_score,
            'heatmap_piece': self.visualization.heatmap_piece,
            'heatmap_intensity': self.visualization.heatmap_intensity,
            'bsp_zone': self.visualization.bsp_zone_type,
            'tactical_motifs': self.tactical_motifs,
            'guardrails_passed': self.guardrails_passed,
            'minimax_threshold_met': self.meets_minimax_threshold,
            'active_methods': [r.method_name for r in self.get_active_methods()],
            'method_results': {
                name: {
                    'status': result.status.value,
                    'value': result.value,
                    'active': result.active_in_board
                }
                for name, result in self.method_results.items()
            }
        }
    
    def should_display_in_ui(self, min_value_threshold: float = 0.1) -> bool:
        """Check if this move should be displayed in the UI based on thresholds."""
        # Display if minimax value > 10% from neutral
        if self.minimax_value is not None:
            if abs(self.minimax_value) > min_value_threshold:
                return True
        
        # Display if any active method gave it a good score
        for result in self.get_active_methods():
            if result.value is not None and abs(result.value) > min_value_threshold:
                return True
        
        # Display if it has tactical motifs
        if self.tactical_motifs:
            return True
        
        # Display if it passed all guardrails and has decent score
        if self.guardrails_passed and self.final_score > min_value_threshold:
            return True
        
        return False
    
    def finalize_evaluation(self, final_score: float, reason: str, confidence: float = 1.0) -> None:
        """Finalize the move evaluation."""
        self.final_score = final_score
        self.primary_reason = reason
        self.confidence = confidence
        self.status = MoveStatus.COMPLETED
        self.total_duration_ms = (time.time() - self.created_at) * 1000
    
    def reject_move(self, reason: str) -> None:
        """Reject the move with a reason."""
        self.status = MoveStatus.REJECTED
        self.primary_reason = reason
        self.total_duration_ms = (time.time() - self.created_at) * 1000
    
    def set_error(self, error_message: str) -> None:
        """Set error status."""
        self.status = MoveStatus.ERROR
        self.primary_reason = error_message
        self.total_duration_ms = (time.time() - self.created_at) * 1000
    
    def get_summary_text(self) -> str:
        """Get a summary text for console/UI display."""
        lines = []
        lines.append(f"Move: {self.move.uci()}")
        lines.append(f"Phase: {self.current_phase.value}")
        lines.append(f"Final Score: {self.final_score:.2f}")
        lines.append(f"Bot: {self.bot_name or 'N/A'}")
        lines.append(f"Reason: {self.primary_reason}")
        lines.append("")
        
        # Active methods
        active = self.get_active_methods()
        if active:
            lines.append("Active Methods:")
            for result in active:
                lines.append(f"  {result}")
        
        # Tactical motifs
        if self.tactical_motifs:
            lines.append(f"Tactical: {', '.join(self.tactical_motifs)}")
        
        # Guardrails
        if not self.guardrails_passed:
            lines.append(f"⚠️ Guardrails: {', '.join(self.guardrails_violations)}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"MoveObject({self.move.uci()} | "
            f"phase={self.current_phase.value} | "
            f"score={self.final_score:.2f} | "
            f"guardrails={'✓' if self.guardrails_passed else '✗'} | "
            f"methods={len(self.method_results)})"
        )


class MoveEvaluationManager:
    """Manages move evaluations throughout the game."""
    
    def __init__(self):
        self.current_move: Optional[MoveObject] = None
        self.move_history: List[MoveObject] = []
        self.evaluation_stats: Dict[str, Any] = {}
    
    def create_move_evaluation(self, move: Move, board: Board, bot_name: str = "") -> MoveObject:
        """Create a new move evaluation."""
        move_eval = MoveObject(
            move=move,
            board_fen=board.fen(),
            move_number=board.fullmove_number,
            color=board.turn,
            san_notation=board.san(move) if board.is_legal(move) else str(move),
            bot_name=bot_name
        )
        
        self.current_move = move_eval
        return move_eval
    
    def finalize_current_move(self) -> None:
        """Finalize the current move and add it to history."""
        if self.current_move:
            self.move_history.append(self.current_move)
            self._update_stats(self.current_move)
            self.current_move = None
    
    def _update_stats(self, move_eval: MoveObject) -> None:
        """Update evaluation statistics."""
        if not self.evaluation_stats:
            self.evaluation_stats = {
                'total_moves': 0,
                'avg_duration_ms': 0.0,
                'bot_usage': {},
                'pattern_matches': 0,
                'guardrails_violations': 0,
                'phase_durations': {},
                'method_usage': {},
                'tactical_motifs': 0
            }
        
        stats = self.evaluation_stats
        stats['total_moves'] += 1
        
        # Update average duration
        total_duration = stats['avg_duration_ms'] * (stats['total_moves'] - 1) + move_eval.total_duration_ms
        stats['avg_duration_ms'] = total_duration / stats['total_moves']
        
        # Update bot usage
        for bot_name in move_eval.get_active_bots():
            stats['bot_usage'][bot_name] = stats['bot_usage'].get(bot_name, 0) + 1
        
        # Update method usage
        for method_name in move_eval.method_results.keys():
            stats['method_usage'][method_name] = stats['method_usage'].get(method_name, 0) + 1
        
        # Update pattern matches
        stats['pattern_matches'] += len(move_eval.pattern_matches)
        
        # Update guardrails violations
        stats['guardrails_violations'] += len(move_eval.guardrails_violations)
        
        # Update tactical motifs
        stats['tactical_motifs'] += len(move_eval.tactical_motifs)
        
        # Update phase durations
        for phase, duration in move_eval.phase_durations.items():
            phase_name = phase.value
            if phase_name not in stats['phase_durations']:
                stats['phase_durations'][phase_name] = {'total': 0.0, 'count': 0, 'avg': 0.0}
            
            phase_stats = stats['phase_durations'][phase_name]
            phase_stats['total'] += duration
            phase_stats['count'] += 1
            phase_stats['avg'] = phase_stats['total'] / phase_stats['count']
    
    def get_recent_moves(self, count: int = 10) -> List[MoveObject]:
        """Get recent move evaluations."""
        return self.move_history[-count:]
    
    def get_bot_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for each bot."""
        bot_performance = {}
        
        for move_eval in self.move_history:
            for bot_name, evaluation_step in move_eval.bot_evaluations.items():
                if bot_name not in bot_performance:
                    bot_performance[bot_name] = {
                        'total_evaluations': 0,
                        'avg_duration_ms': 0.0,
                        'avg_confidence': 0.0,
                        'success_rate': 0.0
                    }
                
                perf = bot_performance[bot_name]
                perf['total_evaluations'] += 1
                
                # Update average duration
                total_duration = perf['avg_duration_ms'] * (perf['total_evaluations'] - 1) + evaluation_step.duration_ms
                perf['avg_duration_ms'] = total_duration / perf['total_evaluations']
                
                # Update average confidence
                total_confidence = perf['avg_confidence'] * (perf['total_evaluations'] - 1) + evaluation_step.confidence
                perf['avg_confidence'] = total_confidence / perf['total_evaluations']
                
                # Update success rate (based on status)
                successes = sum(1 for me in self.move_history 
                              if bot_name in me.bot_evaluations and 
                              me.bot_evaluations[bot_name].status == MoveStatus.COMPLETED)
                perf['success_rate'] = successes / perf['total_evaluations']
        
        return bot_performance
    
    def get_method_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for each evaluation method."""
        method_performance = {}
        
        for move_eval in self.move_history:
            for method_name, method_result in move_eval.method_results.items():
                if method_name not in method_performance:
                    method_performance[method_name] = {
                        'total_evaluations': 0,
                        'avg_duration_ms': 0.0,
                        'avg_confidence': 0.0,
                        'success_rate': 0.0,
                        'active_rate': 0.0
                    }
                
                perf = method_performance[method_name]
                perf['total_evaluations'] += 1
                
                # Update average duration
                total_duration = perf['avg_duration_ms'] * (perf['total_evaluations'] - 1) + method_result.processing_time_ms
                perf['avg_duration_ms'] = total_duration / perf['total_evaluations']
                
                # Update average confidence
                total_confidence = perf['avg_confidence'] * (perf['total_evaluations'] - 1) + method_result.confidence
                perf['avg_confidence'] = total_confidence / perf['total_evaluations']
                
                # Update success rate
                successes = sum(1 for me in self.move_history 
                              if method_name in me.method_results and 
                              me.method_results[method_name].status == MethodStatus.COMPLETED)
                perf['success_rate'] = successes / perf['total_evaluations']
                
                # Update active rate
                active_count = sum(1 for me in self.move_history 
                                if method_name in me.method_results and 
                                me.method_results[method_name].active_in_board)
                perf['active_rate'] = active_count / perf['total_evaluations']
        
        return method_performance
    
    def export_evaluation_data(self) -> Dict[str, Any]:
        """Export all evaluation data for analysis."""
        return {
            'stats': self.evaluation_stats,
            'bot_performance': self.get_bot_performance(),
            'method_performance': self.get_method_performance(),
            'recent_moves': [me.get_evaluation_summary() for me in self.get_recent_moves()],
            'total_moves_evaluated': len(self.move_history)
        }


# Factory function for creating move objects
def create_move_object(move: Move, board: Board, bot_name: str = "") -> MoveObject:
    """Factory function to create a MoveObject from a move and board."""
    return MoveObject(
        move=move,
        board_fen=board.fen(),
        move_number=board.fullmove_number,
        color=board.turn,
        san_notation=board.san(move) if board.is_legal(move) else str(move),
        bot_name=bot_name,
        created_at=time.time()
    )


# Global move evaluation manager instance
move_evaluation_manager = MoveEvaluationManager()


# Backward compatibility aliases
MoveEvaluation = MoveObject  # For existing code that uses MoveEvaluation