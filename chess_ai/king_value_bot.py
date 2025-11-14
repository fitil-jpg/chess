import logging
logger = logging.getLogger(__name__)

import chess
import numpy as np
from typing import Tuple, Optional, Dict, Any

from .chess_bot import ChessBot, calculate_king_value
from utils import GameContext
from core.evaluator import Evaluator

try:
    from utils.heatmap_analyzer import HeatmapAnalyzer
    from utils.heatmap_generator import HeatmapGenerator
    HEATMAP_AVAILABLE = True
except ImportError:
    HEATMAP_AVAILABLE = False
    logger.warning("Heatmap modules not available - using fallback analysis")


class KingValueBot(ChessBot):
    """Variant of :class:`ChessBot` that rewards lowering the opponent's king value
    with enhanced heatmap-based king zone protection.

    The bot uses :func:`calculate_king_value` to compute how a move changes the
    dynamic material value of the enemy king. Additionally, it analyzes heatmap
    patterns around the king to optimize piece placement for king safety and
    opponent pressure.
    """

    def __init__(self, color: bool, enable_heatmaps: bool = True,
                 king_zone_radius: int = 2) -> None:
        super().__init__(color)
        self.enable_heatmaps = enable_heatmaps and HEATMAP_AVAILABLE
        self.king_zone_radius = king_zone_radius
        
        # Initialize heatmap analyzer if available
        if self.enable_heatmaps:
            try:
                self.heatmap_analyzer = HeatmapAnalyzer()
                self.heatmap_generator = HeatmapGenerator()
                logger.info("KingValueBot: heatmap analysis enabled")
            except Exception as e:
                logger.warning(f"KingValueBot: failed to initialize heatmaps: {e}")
                self.enable_heatmaps = False
                self.heatmap_analyzer = None
                self.heatmap_generator = None
        else:
            self.heatmap_analyzer = None
            self.heatmap_generator = None

    def evaluate_move(self, board: chess.Board, move: chess.Move, context: GameContext | None = None):
        score, reason = super().evaluate_move(board, move, context)
        opp_color = not self.color

        # 1) Dynamic king material pressure (existing heuristic)
        before_kv = calculate_king_value(board, opp_color)
        tmp = board.copy(stack=False)
        tmp.push(move)
        after_kv = calculate_king_value(tmp, opp_color)
        kv_delta = before_kv - after_kv
        if kv_delta:
            score += kv_delta
            kv_reason = f"king value pressure (+{kv_delta})"
            reason = f"{reason} | {kv_reason}" if reason else kv_reason

        # 2) Rich king-safety deltas using Evaluator.king_safety
        #    Components include open/semi-open files, attacker counts, pawn storms, proximity.
        self_before_ks = Evaluator.king_safety(board, self.color)
        opp_before_ks = Evaluator.king_safety(board, opp_color)
        self_after_ks = Evaluator.king_safety(tmp, self.color)
        opp_after_ks = Evaluator.king_safety(tmp, opp_color)

        # Positive if we worsened opponent safety (more danger) and improved ours.
        opp_delta = opp_before_ks - opp_after_ks
        self_delta = self_after_ks - self_before_ks

        # Modest weights to keep the signal balanced with base evaluation.
        W_OPP = 4
        W_SELF = 3
        ks_bonus = 0
        if opp_delta:
            ks_bonus += W_OPP * opp_delta
        if self_delta:
            ks_bonus += W_SELF * self_delta
        if ks_bonus:
            score += ks_bonus
            ks_reason = (
                f"king safety Δ (opp {opp_delta:+}, self {self_delta:+}) (+{ks_bonus})"
            )
            reason = f"{reason} | {ks_reason}" if reason else ks_reason

        # 3) Heatmap-based king zone analysis
        if self.enable_heatmaps:
            heatmap_bonus = self._evaluate_king_zone_heatmaps(tmp, move)
            if heatmap_bonus > 0:
                score += heatmap_bonus
                heatmap_reason = f"king zone heatmap (+{heatmap_bonus})"
                reason = f"{reason} | {heatmap_reason}" if reason else heatmap_reason

        return score, reason
    
    def _evaluate_king_zone_heatmaps(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate move based on heatmap analysis of king zones."""
        
        if not self.heatmap_analyzer:
            return 0.0
        
        try:
            # Get king positions
            own_king_sq = board.king(self.color)
            opp_king_sq = board.king(not self.color)
            
            if own_king_sq is None or opp_king_sq is None:
                return 0.0
            
            total_bonus = 0.0
            
            # Analyze own king zone protection
            own_zone_bonus = self._analyze_king_zone_protection(board, own_king_sq, move, defensive=True)
            total_bonus += own_zone_bonus
            
            # Analyze opponent king zone pressure
            opp_zone_bonus = self._analyze_king_zone_protection(board, opp_king_sq, move, defensive=False)
            total_bonus += opp_zone_bonus
            
            return total_bonus
            
        except Exception as e:
            logger.debug(f"KingValueBot: heatmap analysis failed: {e}")
            return 0.0
    
    def _analyze_king_zone_protection(self, board: chess.Board, king_square: chess.Square, 
                                     move: chess.Move, defensive: bool = True) -> float:
        """Analyze king zone using heatmap patterns."""
        
        # Calculate king zone squares
        king_zone = self._get_king_zone_squares(king_square)
        
        if not king_zone:
            return 0.0
        
        # Create simplified heatmap based on piece control
        control_heatmap = self._generate_control_heatmap(board, defensive)
        
        # Analyze zone control
        controlled_squares = 0
        attacked_squares = 0
        
        for square in king_zone:
            if control_heatmap[square] > 0:
                controlled_squares += 1
            elif control_heatmap[square] < 0:
                attacked_squares += 1
        
        # Calculate bonus based on zone control
        zone_size = len(king_zone)
        control_ratio = controlled_squares / max(1, zone_size)
        attack_ratio = attacked_squares / max(1, zone_size)
        
        if defensive:
            # Defensive: reward controlled squares, penalize attacked squares
            bonus = (control_ratio * 100.0) - (attack_ratio * 150.0)
        else:
            # Offensive: reward attacking opponent's king zone
            bonus = attack_ratio * 120.0
        
        # Extra bonus if move directly affects king zone
        if move.to_square in king_zone:
            bonus += 30.0
        
        return max(0.0, bonus if defensive else bonus)
    
    def _get_king_zone_squares(self, king_square: chess.Square) -> list:
        """Get squares within radius of king."""
        
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        zone_squares = []
        
        for df in range(-self.king_zone_radius, self.king_zone_radius + 1):
            for dr in range(-self.king_zone_radius, self.king_zone_radius + 1):
                if df == 0 and dr == 0:
                    continue  # Skip king's own square
                    
                new_file = king_file + df
                new_rank = king_rank + dr
                
                if 0 <= new_file < 8 and 0 <= new_rank < 8:
                    square = chess.square(new_file, new_rank)
                    zone_squares.append(square)
        
        return zone_squares
    
    def _generate_control_heatmap(self, board: chess.Board, defensive: bool) -> np.ndarray:
        """Generate a simple control heatmap for the current position."""
        
        heatmap = np.zeros(64)
        
        if defensive:
            # For defensive analysis: count our piece controls as positive
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.color == self.color:
                    # Add control values for squares this piece attacks/defends
                    attacked = board.attacks(square)
                    for attacked_square in attacked:
                        heatmap[attacked_square] += 1.0
        else:
            # For offensive analysis: count our attacks on opponent as positive
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.color == self.color:
                    # Add control values for squares this piece attacks
                    attacked = board.attacks(square)
                    for attacked_square in attacked:
                        target = board.piece_at(attacked_square)
                        if target and target.color != self.color:
                            heatmap[attacked_square] += 2.0
                        else:
                            heatmap[attacked_square] += 0.5
        
        return heatmap
    
    def get_best_king_zone_move(self, board: chess.Board, context: GameContext | None = None) -> Tuple[Optional[chess.Move], float]:
        """Special method to find best move for king zone improvement."""
        
        if not self.enable_heatmaps:
            return None, 0.0
        
        best_move = None
        best_score = 0.0
        
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.color != self.color:
                continue
            
            tmp = board.copy(stack=False)
            tmp.push(move)
            
            # Evaluate king zone improvement
            heatmap_bonus = self._evaluate_king_zone_heatmaps(tmp, move)
            
            if heatmap_bonus > best_score:
                best_score = heatmap_bonus
                best_move = move
        
        return best_move, best_score


__all__ = ["KingValueBot"]