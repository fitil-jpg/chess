"""AggressiveBot
==================

Very simple aggressive agent that prefers moves with the largest material
gain.  The bot returns a tuple ``(move, confidence)`` where ``confidence`` is
the estimated material advantage after the move.  Non‑capturing moves have
zero confidence.
"""

from __future__ import annotations

import chess

from core.evaluator import Evaluator
from .utility_bot import piece_value


class AggressiveBot:
    def __init__(self, color: bool):
        self.color = color

    def choose_move(self, board: chess.Board, evaluator: Evaluator | None = None, debug: bool = False):
        """Return the move that maximises material gain.

        The second element of the tuple represents the material gain (our
        confidence in the move).  If no capture improves material, a random
        legal move is returned with confidence ``0.0``.
        """

        evaluator = evaluator or Evaluator(board)

        moves = list(board.legal_moves)
        if not moves:
            return None, 0.0

        best_move = None
        best_score = float("-inf")
        for move in moves:
            gain = 0.0
            if board.is_capture(move):
                captured = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if captured and attacker:
                    gain = piece_value(captured) - piece_value(attacker)

            tmp = board.copy(stack=False)
            tmp.push(move)
            score = gain + evaluator.position_score(tmp, self.color)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move, float(best_score)

