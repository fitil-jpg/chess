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

from dataclasses import dataclass
from typing import Dict

import chess


@dataclass
class RiskAnalyzer:
    """Detects moves that hang a piece or lose material.

    The class performs a shallow search (up to two plies after the analysed
    move) using a very small material evaluation.  If every sequence of moves
    results in the moving side having less material than before the move, the
    move is flagged as risky.
    """

    values: Dict[chess.PieceType, int] | None = None

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        if self.values is None:
            self.values = {
                chess.PAWN: 100,
                chess.KNIGHT: 300,
                chess.BISHOP: 300,
                chess.ROOK: 500,
                chess.QUEEN: 900,
                chess.KING: 0,
            }

    # ------------------------------------------------------------------
    def _material(self, board: chess.Board, color: chess.Color) -> int:
        """Return material balance from ``color`` point of view."""

        score = 0
        for piece, val in self.values.items():
            score += len(board.pieces(piece, color)) * val
            score -= len(board.pieces(piece, not color)) * val
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

        if depth == 0 or board.is_game_over():
            stand_pat = self._material(board, color)
            # Quiescence: search further only through captures
            legal = board.generate_legal_moves()
            while beta > alpha:
                try:
                    mv = next(legal)
                except StopIteration:
                    break
                if not board.is_capture(mv):
                    continue
                board.push(mv)
                score = self._search(board, 0, not maximizing, color, alpha, beta)
                board.pop()
                if maximizing:
                    if score > stand_pat:
                        stand_pat = score
                    if stand_pat > alpha:
                        alpha = stand_pat
                else:
                    if score < stand_pat:
                        stand_pat = score
                    if stand_pat < beta:
                        beta = stand_pat
            return stand_pat

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

