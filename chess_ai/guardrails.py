"""Reusable tactical guardrails for candidate move filtering.

This module provides a small set of safety checks intended to prevent
obvious tactical blunders during candidate move selection:

- Legality/sanity: verify the move is legal in the current position
- 1–2 ply blunder check: shallow material-only search to catch simple
  blunders using :class:`RiskAnalyzer`
- High-value hang filter: avoid moves that place high-value pieces on
  squares where they are immediately under-defended

The checks are intentionally lightweight and deterministic. The module is
meant to be used by selectors/orchestrators before running expensive search
or evaluation.
"""

from __future__ import annotations

import chess

from .piece_values import PIECE_VALUES
from .risk_analyzer import RiskAnalyzer


class Guardrails:
    """Tactical guardrails for pruning unsafe moves.

    Parameters
    ----------
    blunder_depth:
        Depth (in plies) for the shallow blunder check after the move.
    high_value_threshold:
        Piece value threshold (centipawns) at or above which the moving
        piece is considered high-value (default: rook and above).
    penalize_instead_of_filter:
        If ``True``, callers may choose to penalize moves instead of
        outright filtering them (this class reports booleans only).
    """

    def __init__(
        self,
        blunder_depth: int = 2,
        high_value_threshold: int = 500,
        penalize_instead_of_filter: bool = False,
    ) -> None:
        self.blunder_depth = max(1, int(blunder_depth))
        self.high_value_threshold = int(high_value_threshold)
        self.penalize_instead_of_filter = bool(penalize_instead_of_filter)
        self._risk = RiskAnalyzer()

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------
    def is_legal_and_sane(self, board: chess.Board, move: chess.Move) -> bool:
        """Return ``True`` if ``move`` is legal and not trivially degenerate.

        This is a defensive check: callers should already iterate over
        ``board.legal_moves``. It ensures the move is legal in the current
        state and that the source and target squares are distinct.
        """

        if move is None:
            return False
        if move.from_square == move.to_square:
            return False
        return move in board.legal_moves

    def is_high_value_hang(self, board: chess.Board, move: chess.Move) -> bool:
        """Return ``True`` if the move likely hangs a high-value piece.

        A move is considered a high-value hang if the moving piece is at or
        above ``high_value_threshold`` and, after the move, the destination
        square is attacked by more enemy pieces than it is defended by our
        pieces. This local attackers-vs-defenders heuristic is fast and
        intentionally conservative.
        """

        piece = board.piece_at(move.from_square)
        if piece is None:
            return False
        if piece.piece_type == chess.KING:
            # The king uses specialized safety rules; skip here.
            return False
        piece_value = PIECE_VALUES.get(piece.piece_type, 0)
        if piece_value < self.high_value_threshold:
            return False

        color = piece.color
        board.push(move)
        try:
            to_sq = move.to_square
            attackers = len(board.attackers(not color, to_sq))
            defenders = len(board.attackers(color, to_sq))
            return attackers > defenders
        finally:
            board.pop()

    def is_blunder(self, board: chess.Board, move: chess.Move) -> bool:
        """Return ``True`` if the shallow search flags the move as risky."""

        return self._risk.is_risky(board, move, depth=self.blunder_depth)

    def allow_move(self, board: chess.Board, move: chess.Move) -> bool:
        """Return ``True`` if the move passes all guardrails."""

        if not self.is_legal_and_sane(board, move):
            return False
        if self.is_high_value_hang(board, move):
            return False
        if self.is_blunder(board, move):
            return False
        return True


__all__ = ["Guardrails"]

