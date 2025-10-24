"""
Move Object - Tracks all parameters and evaluations throughout move pipeline.

This class represents a move candidate as it flows through the evaluation pipeline,
tracking all evaluations, method results, and metadata at each stage.
"""

from __future__ import annotations

import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import chess


class MoveStage(Enum):
    """Stages of move evaluation pipeline."""
    INITIAL = "initial"
    PATTERN_MATCH = "pattern_match"
    WFC_EVAL = "wfc_eval"
    BSP_EVAL = "bsp_eval"
    HEATMAP_EVAL = "heatmap_eval"
    TACTICAL_EVAL = "tactical_eval"
    GUARDRAILS = "guardrails"
    MINIMAX = "minimax"
    FINAL = "final"


class MethodStatus(Enum):
    """Status of method processing."""
    PENDING = "⏳ PENDING"
    PROCESSING = "⚙️ PROCESSING"
    COMPLETED = "✅ COMPLETED"
    SKIPPED = "⏭️ SKIPPED"
    FAILED = "❌ FAILED"


@dataclass
class MethodResult:
    """Result from a single evaluation method."""
    method_name: str
    status: MethodStatus
    value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    active_in_board: bool = False  # Whether this method applies to current position
    timestamp: float = field(default_factory=time.time)
    processing_time_ms: float = 0.0
    
    def __str__(self) -> str:
        active_str = "🟢 ACTIVE" if self.active_in_board else ""
        value_str = f"={self.value:.2f}" if self.value is not None else ""
        return f"{self.status.value} {self.method_name}{value_str} {active_str}"


@dataclass
class MoveObject:
    """
    Represents a move candidate throughout the evaluation pipeline.
    
    Tracks all evaluations, method results, heatmap activations,
    and metadata for visualization and debugging.
    """
    move: chess.Move
    board_fen: str
    current_stage: MoveStage = MoveStage.INITIAL
    
    # Evaluation results from different methods
    method_results: Dict[str, MethodResult] = field(default_factory=dict)
    
    # Score components
    base_score: float = 0.0
    pattern_score: float = 0.0
    wfc_score: float = 0.0
    bsp_score: float = 0.0
    heatmap_score: float = 0.0
    tactical_score: float = 0.0
    positional_score: float = 0.0
    minimax_score: float = 0.0
    final_score: float = 0.0
    
    # Heatmap visualization data
    active_heatmap_piece: Optional[str] = None
    heatmap_intensity: Optional[float] = None
    heatmap_cell_color: str = "red"  # red/blue/purple/green gradient
    
    # BSP zone data
    bsp_zone_type: Optional[str] = None
    bsp_zone_control: Optional[float] = None
    bsp_zone_cells: List[chess.Square] = field(default_factory=list)
    
    # WFC pattern data
    wfc_patterns_matched: List[str] = field(default_factory=list)
    wfc_constraints_satisfied: List[str] = field(default_factory=list)
    
    # Tactical evaluation
    tactical_motifs: List[str] = field(default_factory=list)  # fork, pin, skewer, etc.
    tactical_threats: List[str] = field(default_factory=list)
    
    # Guardrails checks
    guardrails_passed: bool = True
    guardrails_warnings: List[str] = field(default_factory=list)
    
    # Minimax data
    minimax_depth: int = 0
    minimax_value: Optional[float] = None
    minimax_pv: List[chess.Move] = field(default_factory=list)  # Principal variation
    meets_minimax_threshold: bool = False  # value > 10% of neutral
    
    # Metadata
    created_at: float = field(default_factory=time.time)
    evaluation_time_ms: float = 0.0
    bot_name: Optional[str] = None
    reason: str = ""
    confidence: float = 0.0
    
    def add_method_result(
        self,
        method_name: str,
        status: MethodStatus,
        value: Optional[float] = None,
        active: bool = False,
        **metadata
    ) -> None:
        """Add or update a method result."""
        result = MethodResult(
            method_name=method_name,
            status=status,
            value=value,
            metadata=metadata,
            active_in_board=active
        )
        self.method_results[method_name] = result
    
    def update_stage(self, stage: MoveStage) -> None:
        """Update the current evaluation stage."""
        self.current_stage = stage
    
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
    
    def get_active_methods(self) -> List[MethodResult]:
        """Get all methods that are active for this position."""
        return [r for r in self.method_results.values() if r.active_in_board]
    
    def get_method_by_stage(self, stage: MoveStage) -> List[MethodResult]:
        """Get method results by evaluation stage."""
        stage_methods = {
            MoveStage.PATTERN_MATCH: ['PatternResponder', 'OpeningBook'],
            MoveStage.WFC_EVAL: ['WFCEngine'],
            MoveStage.BSP_EVAL: ['BSPEngine'],
            MoveStage.HEATMAP_EVAL: ['HeatmapEval'],
            MoveStage.TACTICAL_EVAL: ['TacticalAnalyzer', 'ThreatGuard'],
            MoveStage.GUARDRAILS: ['Guardrails'],
            MoveStage.MINIMAX: ['Minimax', 'AlphaBeta'],
        }
        
        method_names = stage_methods.get(stage, [])
        return [self.method_results[name] for name in method_names if name in self.method_results]
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get data for visualization in the UI."""
        return {
            'move': self.move.uci(),
            'from_square': self.move.from_square,
            'to_square': self.move.to_square,
            'stage': self.current_stage.value,
            'final_score': self.final_score,
            'heatmap_piece': self.active_heatmap_piece,
            'heatmap_intensity': self.heatmap_intensity,
            'bsp_zone': self.bsp_zone_type,
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
    
    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"MoveObject({self.move.uci()} | "
            f"stage={self.current_stage.value} | "
            f"score={self.final_score:.2f} | "
            f"guardrails={'✓' if self.guardrails_passed else '✗'} | "
            f"methods={len(self.method_results)})"
        )
    
    def get_summary_text(self) -> str:
        """Get a summary text for console/UI display."""
        lines = []
        lines.append(f"Move: {self.move.uci()}")
        lines.append(f"Stage: {self.current_stage.value}")
        lines.append(f"Final Score: {self.final_score:.2f}")
        lines.append(f"Bot: {self.bot_name or 'N/A'}")
        lines.append(f"Reason: {self.reason}")
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
            lines.append(f"⚠️ Guardrails: {', '.join(self.guardrails_warnings)}")
        
        return "\n".join(lines)


def create_move_object(move: chess.Move, board: chess.Board, bot_name: str = "") -> MoveObject:
    """Factory function to create a MoveObject from a move and board."""
    return MoveObject(
        move=move,
        board_fen=board.fen(),
        bot_name=bot_name,
        created_at=time.time()
    )


__all__ = ["MoveObject", "MoveStage", "MethodStatus", "MethodResult", "create_move_object"]
