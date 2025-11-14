"""Utility for shallow tactical risk checks.

This module contains :class:`RiskAnalyzer` which performs a very small
look‑ahead (1–2 plies) after a tentative move.  The goal is not to play
perfect chess but merely to detect obviously hanging moves – situations
where a piece is lost immediately or after a single forced reply.

The implementation uses a tiny negamax style search limited to material
counting.  If the worst result after the opponent's best reply leaves the
moving side with less material than before, the move is considered risky.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import chess
from typing import Dict, List, Tuple, Optional

import logging
logger = logging.getLogger(__name__)

from .piece_values import PIECE_VALUES


@dataclass
class MoveAnalysisStats:
    """Statistics for a single move analysis."""
    move_uci: str
    depth_analyzed: int
    is_risky: bool
    material_before: int
    material_after: int
    attackers_count: int
    defenders_count: int
    search_nodes: int = 0
    rejection_reason: str = ""
    analysis_time_ms: float = 0.0


@dataclass
class MoveAnalysisSummary:
    """Comprehensive summary of move analysis for a position."""
    total_moves_evaluated: int
    safe_moves_found: int
    risky_moves_rejected: int
    chosen_move: Optional[str]
    chosen_by_bot: bool
    analysis_depth: int
    total_search_nodes: int
    rejection_reasons: Dict[str, int] = field(default_factory=dict)
    analysis_time_total_ms: float = 0.0
    pattern_description: str = ""


@dataclass
class RiskAnalyzer:
    """Detects moves that hang a piece or lose material.

    The class performs a shallow search (up to two plies after the analysed
    move) using a very small material evaluation.  If every sequence of moves
    results in the moving side having less material than before the move, the
    move is flagged as risky.
    """

    def __init__(self):
        self.move_stats: List[MoveAnalysisStats] = []
        self.current_analysis_depth = 2
        self._search_node_count = 0

    # ------------------------------------------------------------------
    def _material(self, board: chess.Board, color: chess.Color) -> int:
        """Return material balance from ``color`` point of view."""

        score = 0
        from .chess_bot import calculate_king_value

        wking = calculate_king_value(board, chess.WHITE)
        bking = calculate_king_value(board, chess.BLACK)
        for _, piece in board.piece_map().items():
            if piece.piece_type == chess.KING:
                val = wking if piece.color == chess.WHITE else bking
            else:
                val = PIECE_VALUES[piece.piece_type]
            score += val if piece.color == color else -val
        return score

    def _search(
        self,
        board: chess.Board,
        depth: int,
        maximizing: bool,
        color: chess.Color,
        alpha: float,
        beta: float,
    ) -> int:
        """Tiny negamax search with alpha-beta pruning."""
        self._search_node_count += 1

        if depth <= 0 or board.is_game_over():
            return self._material(board, color)

        if maximizing:
            best = -float("inf")
            legal = board.generate_legal_moves()
            while beta > alpha:
                try:
                    mv = next(legal)
                except StopIteration:
                    break
                board.push(mv)
                to_sq = mv.to_square
                attackers = len(board.attackers(not color, to_sq))
                defenders = len(board.attackers(color, to_sq))
                if attackers > defenders:
                    score = -float("inf")
                else:
                    score = self._search(board, depth - 1, False, color, alpha, beta)
                board.pop()
                if score > best:
                    best = score
                if best > alpha:
                    alpha = best
            if best == -float("inf"):
                return self._material(board, color)
            return best
        else:
            best = float("inf")
            legal = board.generate_legal_moves()
            while beta > alpha:
                try:
                    mv = next(legal)
                except StopIteration:
                    break
                board.push(mv)
                to_sq = mv.to_square
                attackers = len(board.attackers(color, to_sq))
                defenders = len(board.attackers(not color, to_sq))
                if attackers > defenders:
                    score = float("inf")
                else:
                    score = self._search(board, depth - 1, True, color, alpha, beta)
                board.pop()
                if score < best:
                    best = score
                if best < beta:
                    beta = best
            if best == float("inf"):
                return self._material(board, color)
            return best

    # ------------------------------------------------------------------
    def is_risky(self, board: chess.Board, move: chess.Move, depth: int = 2) -> bool:
        """Return ``True`` if the move likely loses material.

        Parameters
        ----------
        board:
            Current board state.  The board is restored to its original state
            after analysis.
        move:
            Move to be checked.
        depth:
            Additional plies to analyse after the move.  Default two plies
            (opponent reply and our best recapture).
        """

        color = board.turn
        logger.debug(
            "AI-Technique AlphaBeta(Shallow): risk_check move=%s depth=%d",
            move.uci() if hasattr(move, 'uci') else str(move),
            depth,
        )
        before = self._material(board, color)

        board.push(move)
        sq = move.to_square
        attackers = len(board.attackers(not color, sq))
        defenders = len(board.attackers(color, sq))
        if attackers > defenders:
            board.pop()
            return True

        worst = self._search(
            board,
            depth - 1,
            maximizing=False,
            color=color,
            alpha=-float("inf"),
            beta=float("inf"),
        )
        board.pop()

        return worst < before

    def analyze_move(self, board: chess.Board, move: chess.Move, depth: int = 2) -> MoveAnalysisStats:
        """Comprehensive analysis of a single move with detailed statistics."""
        import time
        start_time = time.monotonic()
        
        self._search_node_count = 0
        color = board.turn
        before = self._material(board, color)
        
        # Count attackers and defenders before move
        piece_at_from = board.piece_at(move.from_square)
        piece_at_to = board.piece_at(move.to_square)
        
        board.push(move)
        sq = move.to_square
        attackers = len(board.attackers(not color, sq))
        defenders = len(board.attackers(color, sq))
        after = self._material(board, color)
        
        # Determine if risky and get reason
        is_risky = False
        rejection_reason = ""
        
        if attackers > defenders:
            is_risky = True
            rejection_reason = f"Piece under attack (attackers:{attackers} > defenders:{defenders})"
        else:
            worst = self._search(
                board,
                depth - 1,
                maximizing=False,
                color=color,
                alpha=-float("inf"),
                beta=float("inf"),
            )
            if worst < before:
                is_risky = True
                rejection_reason = f"Material loss expected: {before}→{worst} ({before-worst})"
        
        board.pop()
        
        analysis_time = (time.monotonic() - start_time) * 1000  # Convert to milliseconds
        
        stats = MoveAnalysisStats(
            move_uci=move.uci(),
            depth_analyzed=depth,
            is_risky=is_risky,
            material_before=before,
            material_after=after,
            attackers_count=attackers,
            defenders_count=defenders,
            search_nodes=self._search_node_count,
            rejection_reason=rejection_reason,
            analysis_time_ms=analysis_time
        )
        
        self.move_stats.append(stats)
        return stats

    def analyze_position(self, board: chess.Board, depth: int = 2, chosen_move: Optional[chess.Move] = None, chosen_by_bot: bool = False) -> MoveAnalysisSummary:
        """Analyze all legal moves in a position and return comprehensive summary."""
        import time
        start_time = time.monotonic()
        
        self.move_stats.clear()
        self.current_analysis_depth = depth
        total_nodes = 0
        
        legal_moves = list(board.legal_moves)
        risky_count = 0
        safe_count = 0
        rejection_reasons: Dict[str, int] = {}
        
        for move in legal_moves:
            stats = self.analyze_move(board, move, depth)
            total_nodes += stats.search_nodes
            
            if stats.is_risky:
                risky_count += 1
                reason_key = stats.rejection_reason.split('(')[0].strip()  # Categorize by main reason
                rejection_reasons[reason_key] = rejection_reasons.get(reason_key, 0) + 1
            else:
                safe_count += 1
        
        total_time = (time.monotonic() - start_time) * 1000
        
        # Generate pattern description
        pattern_desc = self._generate_pattern_description(board, safe_count, risky_count)
        
        summary = MoveAnalysisSummary(
            total_moves_evaluated=len(legal_moves),
            safe_moves_found=safe_count,
            risky_moves_rejected=risky_count,
            chosen_move=chosen_move.uci() if chosen_move else None,
            chosen_by_bot=chosen_by_bot,
            analysis_depth=depth,
            total_search_nodes=total_nodes,
            rejection_reasons=rejection_reasons,
            analysis_time_total_ms=total_time,
            pattern_description=pattern_desc
        )
        
        # Log comprehensive analysis
        self._log_analysis_summary(summary)
        
        return summary

    def _generate_pattern_description(self, board: chess.Board, safe_moves: int, risky_moves: int) -> str:
        """Generate automatic pattern description based on position analysis."""
        total_moves = safe_moves + risky_moves
        if total_moves == 0:
            return "No legal moves available"
        
        risk_ratio = risky_moves / total_moves
        
        # Analyze position characteristics
        material_imbalance = abs(self._material(board, chess.WHITE) - self._material(board, chess.BLACK))
        is_endgame = len(board.piece_map()) < 20
        is_middlegame = not is_endgame and len(board.piece_map()) < 32
        
        if risk_ratio > 0.7:
            tactical_state = "highly tactical position with many risks"
        elif risk_ratio > 0.4:
            tactical_state = "moderately tactical position"
        else:
            tactical_state = "relatively quiet position"
        
        phase = "endgame" if is_endgame else "middlegame" if is_middlegame else "opening"
        material_desc = f"significant material imbalance" if material_imbalance > 500 else "roughly equal material"
        
        return f"{phase.title()} with {tactical_state} and {material_desc}. {safe_moves} safe moves found, {risky_moves} risky moves identified."

    def _log_analysis_summary(self, summary: MoveAnalysisSummary):
        """Log comprehensive analysis summary."""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE MOVE ANALYSIS SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total moves evaluated: {summary.total_moves_evaluated}")
        logger.info(f"Safe moves found: {summary.safe_moves_found}")
        logger.info(f"Risky moves rejected: {summary.risky_moves_rejected}")
        logger.info(f"Analysis depth: {summary.analysis_depth}")
        logger.info(f"Total search nodes: {summary.total_search_nodes}")
        logger.info(f"Analysis time: {summary.analysis_time_total_ms:.2f}ms")
        
        if summary.chosen_move:
            bot_type = "Bot decision" if summary.chosen_by_bot else "Manual selection"
            logger.info(f"Chosen move: {summary.chosen_move} ({bot_type})")
        
        if summary.rejection_reasons:
            logger.info("Rejection reasons:")
            for reason, count in summary.rejection_reasons.items():
                logger.info(f"  - {reason}: {count} moves")
        
        logger.info(f"Pattern analysis: {summary.pattern_description}")
        
        # Detailed move breakdown
        safe_moves = [s for s in self.move_stats if not s.is_risky]
        risky_moves = [s for s in self.move_stats if s.is_risky]
        
        if safe_moves:
            logger.info("Safe moves (ranked by material gain):")
            safe_moves.sort(key=lambda x: x.material_after - x.material_before, reverse=True)
            for i, stat in enumerate(safe_moves[:5]):  # Top 5 safe moves
                material_diff = stat.material_after - stat.material_before
                logger.info(f"  {i+1}. {stat.move_uci}: material {'+' if material_diff >= 0 else ''}{material_diff}, "
                          f"attackers:{stat.attackers_count}, defenders:{stat.defenders_count}, "
                          f"nodes:{stat.search_nodes}, time:{stat.analysis_time_ms:.2f}ms")
        
        if risky_moves:
            logger.info("Risky moves (sample):")
            for i, stat in enumerate(risky_moves[:3]):  # Sample 3 risky moves
                logger.info(f"  {i+1}. {stat.move_uci}: {stat.rejection_reason}, "
                          f"nodes:{stat.search_nodes}, time:{stat.analysis_time_ms:.2f}ms")
        
        logger.info("=" * 80)
