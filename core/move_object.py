"""
Comprehensive Move Object for Chess AI Evaluation Tracking.

This module provides a Move object that tracks all evaluation data throughout
the move selection pipeline, including bot decisions, pattern matching,
WFC/BSP analysis, and visualization states.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import chess
from chess import Move, Board, Square


class MovePhase(Enum):
    """Phases of move evaluation."""
    INITIALIZATION = "initialization"
    PATTERN_MATCHING = "pattern_matching"
    WFC_ANALYSIS = "wfc_analysis"
    BSP_ANALYSIS = "bsp_analysis"
    BOT_EVALUATION = "bot_evaluation"
    GUARDRAILS_CHECK = "guardrails_check"
    FINAL_SELECTION = "final_selection"
    VISUALIZATION = "visualization"


class MoveStatus(Enum):
    """Status of move evaluation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    ERROR = "error"


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
class VisualizationState:
    """Tracks visualization state for the move."""
    heatmap_piece: Optional[str] = None
    heatmap_set: Optional[str] = None
    highlighted_squares: Set[Square] = field(default_factory=set)
    zone_colors: Dict[str, str] = field(default_factory=dict)  # zone_type -> color
    current_cell: Optional[Square] = None  # For real-time visualization
    bsp_zones: List[Dict[str, Any]] = field(default_factory=list)
    wfc_patterns: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MoveEvaluation:
    """Comprehensive move evaluation object."""
    
    # Basic move information
    move: Move
    board_fen: str
    move_number: int
    color: chess.Color
    san_notation: str = ""
    
    # Evaluation pipeline tracking
    phase: MovePhase = MovePhase.INITIALIZATION
    status: MoveStatus = MoveStatus.PENDING
    evaluation_steps: List[EvaluationStep] = field(default_factory=list)
    
    # Timing information
    created_at: float = field(default_factory=time.time)
    total_duration_ms: float = 0.0
    phase_durations: Dict[MovePhase, float] = field(default_factory=dict)
    
    # Evaluation results
    final_score: float = 0.0
    confidence: float = 0.0
    primary_reason: str = ""
    contributing_factors: Dict[str, float] = field(default_factory=dict)
    
    # Pattern and engine analysis
    pattern_matches: List[Dict[str, Any]] = field(default_factory=list)
    wfc_analysis: Dict[str, Any] = field(default_factory=dict)
    bsp_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Bot evaluations
    bot_evaluations: Dict[str, EvaluationStep] = field(default_factory=dict)
    
    # Guardrails and safety
    guardrails_passed: bool = True
    guardrails_violations: List[str] = field(default_factory=list)
    
    # Visualization state
    visualization: VisualizationState = field(default_factory=VisualizationState)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_evaluation_step(self, step: EvaluationStep) -> None:
        """Add an evaluation step to the pipeline."""
        step.timestamp = time.time()
        self.evaluation_steps.append(step)
        
        if step.bot_name:
            self.bot_evaluations[step.bot_name] = step
    
    def start_phase(self, phase: MovePhase) -> None:
        """Start a new evaluation phase."""
        self.phase = phase
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
    
    def update_visualization(self, **kwargs) -> None:
        """Update visualization state."""
        for key, value in kwargs.items():
            if hasattr(self.visualization, key):
                setattr(self.visualization, key, value)
    
    def get_active_bots(self) -> List[str]:
        """Get list of bots that evaluated this move."""
        return list(self.bot_evaluations.keys())
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get a summary of the evaluation process."""
        return {
            'move': self.san_notation or str(self.move),
            'phase': self.phase.value,
            'status': self.status.value,
            'total_duration_ms': self.total_duration_ms,
            'final_score': self.final_score,
            'confidence': self.confidence,
            'primary_reason': self.primary_reason,
            'active_bots': self.get_active_bots(),
            'pattern_matches': len(self.pattern_matches),
            'guardrails_passed': self.guardrails_passed,
            'violations': len(self.guardrails_violations)
        }
    
    def get_timing_breakdown(self) -> Dict[str, float]:
        """Get timing breakdown by phase."""
        return {phase.value: duration for phase, duration in self.phase_durations.items()}
    
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


class MoveEvaluationManager:
    """Manages move evaluations throughout the game."""
    
    def __init__(self):
        self.current_move: Optional[MoveEvaluation] = None
        self.move_history: List[MoveEvaluation] = []
        self.evaluation_stats: Dict[str, Any] = {}
    
    def create_move_evaluation(self, move: Move, board: Board) -> MoveEvaluation:
        """Create a new move evaluation."""
        move_eval = MoveEvaluation(
            move=move,
            board_fen=board.fen(),
            move_number=board.fullmove_number,
            color=board.turn,
            san_notation=board.san(move) if board.is_legal(move) else str(move)
        )
        
        self.current_move = move_eval
        return move_eval
    
    def finalize_current_move(self) -> None:
        """Finalize the current move and add it to history."""
        if self.current_move:
            self.move_history.append(self.current_move)
            self._update_stats(self.current_move)
            self.current_move = None
    
    def _update_stats(self, move_eval: MoveEvaluation) -> None:
        """Update evaluation statistics."""
        if not self.evaluation_stats:
            self.evaluation_stats = {
                'total_moves': 0,
                'avg_duration_ms': 0.0,
                'bot_usage': {},
                'pattern_matches': 0,
                'guardrails_violations': 0,
                'phase_durations': {}
            }
        
        stats = self.evaluation_stats
        stats['total_moves'] += 1
        
        # Update average duration
        total_duration = stats['avg_duration_ms'] * (stats['total_moves'] - 1) + move_eval.total_duration_ms
        stats['avg_duration_ms'] = total_duration / stats['total_moves']
        
        # Update bot usage
        for bot_name in move_eval.get_active_bots():
            stats['bot_usage'][bot_name] = stats['bot_usage'].get(bot_name, 0) + 1
        
        # Update pattern matches
        stats['pattern_matches'] += len(move_eval.pattern_matches)
        
        # Update guardrails violations
        stats['guardrails_violations'] += len(move_eval.guardrails_violations)
        
        # Update phase durations
        for phase, duration in move_eval.phase_durations.items():
            phase_name = phase.value
            if phase_name not in stats['phase_durations']:
                stats['phase_durations'][phase_name] = {'total': 0.0, 'count': 0, 'avg': 0.0}
            
            phase_stats = stats['phase_durations'][phase_name]
            phase_stats['total'] += duration
            phase_stats['count'] += 1
            phase_stats['avg'] = phase_stats['total'] / phase_stats['count']
    
    def get_recent_moves(self, count: int = 10) -> List[MoveEvaluation]:
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
    
    def export_evaluation_data(self) -> Dict[str, Any]:
        """Export all evaluation data for analysis."""
        return {
            'stats': self.evaluation_stats,
            'bot_performance': self.get_bot_performance(),
            'recent_moves': [me.get_evaluation_summary() for me in self.get_recent_moves()],
            'total_moves_evaluated': len(self.move_history)
        }


# Global move evaluation manager instance
move_evaluation_manager = MoveEvaluationManager()
