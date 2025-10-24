"""
Hybrid Bot - Integrates WFC, BSP, Heatmaps, and Tactical Evaluation

This bot combines multiple evaluation methods:
- WFC (Wave Function Collapse) for pattern-based move generation
- BSP (Binary Space Partitioning) for zone control analysis
- Heatmap evaluation for piece positioning
- Tactical analysis for tactical motifs
- Guardrails for safety checks
- Minimax for depth search

Each move is tracked through the MoveObject pipeline for full visibility.
"""

import time
import logging
from typing import Optional, List, Dict, Tuple
import chess
import random

from core.move_object import MoveObject, MoveStage, MethodStatus, create_move_object
from chess_ai.wfc_engine import WFCEngine, create_chess_wfc_engine, ChessPattern
from chess_ai.bsp_engine import BSPEngine, create_chess_bsp_engine
from chess_ai.guardrails import Guardrails
from utils.timing_config import get_timing_config

logger = logging.getLogger(__name__)


class HybridBot:
    """
    Hybrid chess bot integrating WFC, BSP, and tactical evaluation.
    
    This bot demonstrates the full evaluation pipeline with move tracking.
    """
    
    def __init__(self, color: chess.Color):
        self.color = color
        self.name = f"HybridBot ({'W' if color == chess.WHITE else 'B'})"
        
        # Initialize engines
        self.wfc_engine = create_chess_wfc_engine()
        self.bsp_engine = create_chess_bsp_engine()
        self.guardrails = Guardrails(blunder_depth=2, high_value_threshold=500)
        self.config = get_timing_config()
        
        # Tracking
        self.last_move_obj: Optional[MoveObject] = None
        self.last_reason: str = ""
        self.last_features: Optional[Dict] = None
        self.current_bot_name: str = self.name
    
    def choose_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Choose the best move using hybrid evaluation."""
        start_time = time.time()
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        # Create move objects for all candidates
        move_candidates: List[MoveObject] = []
        for move in legal_moves:
            move_obj = create_move_object(move, board, self.name)
            move_candidates.append(move_obj)
        
        # Evaluate each candidate through the pipeline
        for move_obj in move_candidates:
            self._evaluate_move_pipeline(move_obj, board)
        
        # Select best move
        best_move_obj = max(move_candidates, key=lambda m: m.final_score)
        
        # Track for visualization
        self.last_move_obj = best_move_obj
        self.last_reason = best_move_obj.reason
        self.last_features = best_move_obj.get_visualization_data()
        
        # Update current bot name to show which engine was primary
        primary_engine = self._get_primary_engine(best_move_obj)
        self.current_bot_name = f"{self.name} > {primary_engine}"
        
        elapsed_ms = (time.time() - start_time) * 1000
        best_move_obj.evaluation_time_ms = elapsed_ms
        
        logger.info(
            f"{self.current_bot_name} chose {best_move_obj.move.uci()} "
            f"(score={best_move_obj.final_score:.2f}, time={elapsed_ms:.1f}ms)"
        )
        
        return best_move_obj.move
    
    def _evaluate_move_pipeline(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate a move through the full pipeline."""
        # Stage 1: Pattern Matching (WFC)
        move_obj.update_stage(MoveStage.PATTERN_MATCH)
        self._evaluate_patterns(move_obj, board)
        
        # Stage 2: WFC Evaluation
        move_obj.update_stage(MoveStage.WFC_EVAL)
        self._evaluate_wfc(move_obj, board)
        
        # Stage 3: BSP Evaluation
        move_obj.update_stage(MoveStage.BSP_EVAL)
        self._evaluate_bsp(move_obj, board)
        
        # Stage 4: Heatmap Evaluation
        move_obj.update_stage(MoveStage.HEATMAP_EVAL)
        self._evaluate_heatmap(move_obj, board)
        
        # Stage 5: Tactical Evaluation
        move_obj.update_stage(MoveStage.TACTICAL_EVAL)
        self._evaluate_tactical(move_obj, board)
        
        # Stage 6: Guardrails
        move_obj.update_stage(MoveStage.GUARDRAILS)
        self._evaluate_guardrails(move_obj, board)
        
        # Stage 7: Minimax
        move_obj.update_stage(MoveStage.MINIMAX)
        self._evaluate_minimax(move_obj, board)
        
        # Stage 8: Final score calculation
        move_obj.update_stage(MoveStage.FINAL)
        move_obj.calculate_final_score()
        
        # Set reason based on dominant factor
        move_obj.reason = self._generate_reason(move_obj)
    
    def _evaluate_patterns(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate using pattern matching."""
        start = time.time()
        
        # Simple pattern evaluation based on piece and square
        piece = board.piece_at(move_obj.move.from_square)
        if not piece:
            move_obj.add_method_result("PatternResponder", MethodStatus.SKIPPED)
            return
        
        # Check if move matches COW opening patterns
        is_opening = board.fullmove_number <= 10
        is_central = chess.square_file(move_obj.move.to_square) in [3, 4]
        
        score = 0.0
        if is_opening and is_central:
            score = 0.8
            move_obj.wfc_patterns_matched.append("COW_opening")
        
        move_obj.pattern_score = score
        processing_time = (time.time() - start) * 1000
        
        move_obj.add_method_result(
            "PatternResponder",
            MethodStatus.COMPLETED,
            value=score,
            active=is_opening,
            processing_time_ms=processing_time,
            patterns_matched=len(move_obj.wfc_patterns_matched)
        )
    
    def _evaluate_wfc(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate using WFC engine."""
        start = time.time()
        
        # Simplified WFC evaluation
        # In full implementation, this would generate patterns and match
        score = random.uniform(0.3, 0.7)  # Placeholder
        
        move_obj.wfc_score = score
        processing_time = (time.time() - start) * 1000
        
        move_obj.add_method_result(
            "WFCEngine",
            MethodStatus.COMPLETED,
            value=score,
            active=True,
            processing_time_ms=processing_time
        )
    
    def _evaluate_bsp(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate using BSP engine."""
        start = time.time()
        
        # Analyze zones
        zone_stats = self.bsp_engine.analyze_board(board)
        zone = self.bsp_engine.get_zone_for_square(move_obj.move.to_square)
        
        if zone:
            move_obj.bsp_zone_type = zone.zone_type
            move_obj.bsp_zone_cells = zone.get_squares_in_zone()
            
            # Score based on zone importance
            zone_importance = self.bsp_engine._get_zone_importance(zone.zone_type or "general")
            score = zone_importance / 2.0  # Normalize to 0-1
            move_obj.bsp_score = score
            move_obj.bsp_zone_control = zone_importance
        else:
            score = 0.5
            move_obj.bsp_score = score
        
        processing_time = (time.time() - start) * 1000
        
        move_obj.add_method_result(
            "BSPEngine",
            MethodStatus.COMPLETED,
            value=score,
            active=zone is not None,
            processing_time_ms=processing_time,
            zone_type=move_obj.bsp_zone_type
        )
    
    def _evaluate_heatmap(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate using heatmap data."""
        start = time.time()
        
        piece = board.piece_at(move_obj.move.from_square)
        if not piece:
            move_obj.add_method_result("HeatmapEval", MethodStatus.SKIPPED)
            return
        
        # Simplified heatmap evaluation
        piece_names = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king"
        }
        
        piece_name = piece_names.get(piece.piece_type)
        move_obj.active_heatmap_piece = piece_name
        
        # Simulate heatmap intensity (in real implementation, load from heatmap data)
        move_obj.heatmap_intensity = random.uniform(0.4, 0.9)
        score = move_obj.heatmap_intensity
        move_obj.heatmap_score = score
        
        processing_time = (time.time() - start) * 1000
        
        move_obj.add_method_result(
            "HeatmapEval",
            MethodStatus.COMPLETED,
            value=score,
            active=True,
            processing_time_ms=processing_time,
            piece=piece_name
        )
    
    def _evaluate_tactical(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate tactical elements."""
        start = time.time()
        
        # Check for tactical motifs
        score = 0.5
        
        # Check if move gives check
        board.push(move_obj.move)
        if board.is_check():
            move_obj.tactical_motifs.append("check")
            score += 0.3
        
        # Check if move captures
        if board.is_capture(move_obj.move):
            move_obj.tactical_motifs.append("capture")
            score += 0.2
        
        board.pop()
        
        move_obj.tactical_score = score
        processing_time = (time.time() - start) * 1000
        
        move_obj.add_method_result(
            "TacticalAnalyzer",
            MethodStatus.COMPLETED,
            value=score,
            active=len(move_obj.tactical_motifs) > 0,
            processing_time_ms=processing_time,
            motifs=move_obj.tactical_motifs
        )
    
    def _evaluate_guardrails(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate with guardrails checks."""
        start = time.time()
        
        passed = self.guardrails.allow_move(board, move_obj.move)
        move_obj.guardrails_passed = passed
        
        if not passed:
            if not self.guardrails.is_legal_and_sane(board, move_obj.move):
                move_obj.guardrails_warnings.append("illegal_move")
            if self.guardrails.is_high_value_hang(board, move_obj.move):
                move_obj.guardrails_warnings.append("high_value_hang")
            if self.guardrails.is_blunder(board, move_obj.move):
                move_obj.guardrails_warnings.append("blunder")
        
        processing_time = (time.time() - start) * 1000
        
        move_obj.add_method_result(
            "Guardrails",
            MethodStatus.COMPLETED,
            value=1.0 if passed else 0.0,
            active=True,
            processing_time_ms=processing_time,
            passed=passed,
            warnings=len(move_obj.guardrails_warnings)
        )
    
    def _evaluate_minimax(self, move_obj: MoveObject, board: chess.Board):
        """Evaluate using simplified minimax."""
        start = time.time()
        
        # Simplified minimax (in real implementation, use full minimax/alpha-beta)
        board.push(move_obj.move)
        
        # Simple material evaluation
        value = self._simple_material_eval(board)
        move_obj.minimax_value = value
        move_obj.minimax_depth = 1
        
        # Check if meets 10% threshold
        threshold = self.config.minimax_threshold_percent / 100.0
        move_obj.meets_minimax_threshold = abs(value) > threshold
        
        board.pop()
        
        move_obj.minimax_score = (value + 1.0) / 2.0  # Normalize to 0-1
        processing_time = (time.time() - start) * 1000
        
        move_obj.add_method_result(
            "Minimax",
            MethodStatus.COMPLETED,
            value=value,
            active=move_obj.meets_minimax_threshold,
            processing_time_ms=processing_time,
            depth=1
        )
    
    def _simple_material_eval(self, board: chess.Board) -> float:
        """Simple material evaluation."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                score += value if piece.color == self.color else -value
        
        return score / 50.0  # Normalize
    
    def _get_primary_engine(self, move_obj: MoveObject) -> str:
        """Determine which engine was most influential."""
        scores = {
            'WFC': move_obj.wfc_score,
            'BSP': move_obj.bsp_score,
            'Heatmap': move_obj.heatmap_score,
            'Tactical': move_obj.tactical_score,
            'Minimax': move_obj.minimax_score
        }
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _generate_reason(self, move_obj: MoveObject) -> str:
        """Generate a human-readable reason for the move."""
        reasons = []
        
        if move_obj.wfc_patterns_matched:
            reasons.append(f"COW_OPENING({len(move_obj.wfc_patterns_matched)})")
        
        if move_obj.bsp_zone_type:
            reasons.append(f"BSP_{move_obj.bsp_zone_type.upper()}")
        
        if move_obj.tactical_motifs:
            reasons.append(f"TACTICAL_{','.join(move_obj.tactical_motifs).upper()}")
        
        if move_obj.meets_minimax_threshold:
            reasons.append(f"MINIMAX>{self.config.minimax_threshold_percent}%")
        
        if not move_obj.guardrails_passed:
            reasons.append("⚠️GUARDRAIL_WARNING")
        
        return " | ".join(reasons) if reasons else "POSITIONAL"
    
    def get_last_reason(self) -> str:
        """Get the reason for the last move."""
        return self.last_reason
    
    def get_last_features(self) -> Optional[Dict]:
        """Get features from the last move."""
        return self.last_features


__all__ = ["HybridBot"]
