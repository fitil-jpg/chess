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
from utils import GameContext
from .utility_bot import piece_value


_SHARED_EVALUATOR: Evaluator | None = None


class AggressiveBot:
    def __init__(self, color: bool, capture_gain_factor: float = 1.5):
        self.color = color
        # Scaling applied to capture gains when we're behind in material.
        self.capture_gain_factor = capture_gain_factor

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return the move that maximises material gain.

        Parameters
        ----------
        board: chess.Board
            Current board state.
        context: GameContext | None, optional
            Shared game context (currently unused).
        evaluator: Evaluator | None, optional
            Reusable evaluator.  If ``None``, a shared instance is created.
        debug: bool, optional
            Unused flag for API compatibility.

        Returns
        -------
        tuple[chess.Move | None, float]
            Selected move and the estimated material gain.
        """

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

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
                    # Encourage trades when behind by boosting capture gains.
                    if context and context.material_diff < 0:
                        gain *= self.capture_gain_factor
                        if debug:
                            print(
                                f"AggressiveBot: material deficit, "
                                f"scaled capture gain to {gain:.1f}"
                            )

            tmp = board.copy(stack=False)
            tmp.push(move)
            score = gain + evaluator.position_score(tmp, self.color)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move, float(best_score)

