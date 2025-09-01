from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import chess

from core.evaluator import Evaluator


class CriticalBot:
    """Agent that targets high-threat opponent pieces.

    The bot uses :class:`Evaluator.criticality` to identify the most critical
    opponent pieces and prefers moves that capture them.  If no such capture is
    available the bot yields ``(None, 0.0)`` allowing other agents to decide.
    """

    def __init__(self, color: bool, capture_bonus: float = 100.0) -> None:
        self.color = color
        self.capture_bonus = capture_bonus

    def choose_move(
        self,
        board: chess.Board,
        context=None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        evaluator = evaluator or Evaluator(board)
        critical = evaluator.criticality(board, self.color)
        if not critical:
            return None, 0.0
        critical_squares = {sq for sq, _ in critical}

        best_move = None
        best_score = float("-inf")
        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.color != self.color:
                continue
            score = 0.0
            if move.to_square in critical_squares and board.piece_at(move.to_square):
                score += self.capture_bonus
            if score > best_score:
                best_score = score
                best_move = move

        if best_move is None or best_score <= 0.0:
            return None, 0.0
        if debug:
            logger.debug(
                f"CriticalBot selects {best_move} with score {best_score}"
            )
        return best_move, best_score