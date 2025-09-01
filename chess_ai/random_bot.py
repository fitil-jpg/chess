import logging
logger = logging.getLogger(__name__)

import random

from core.evaluator import Evaluator
from utils import GameContext


_SHARED_EVALUATOR: Evaluator | None = None
# Small tweak applied when mobility differs between the sides.
# The bot slightly prefers positions where it has more mobility and
# de-emphasises ones with less, based only on the sign of the mobility.
MOBILITY_FACTOR = 0.01


class RandomBot:
    def __init__(self, color: bool):
        self.color = color

    def choose_move(
        self,
        board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return a random legal move adjusted by position evaluation.

        Parameters
        ----------
        board: chess.Board
            Position to analyse.
        context: GameContext | None, optional
            Shared game context (unused).
        evaluator: Evaluator | None, optional
            Reusable evaluator.  A shared one is created if ``None``.
        debug: bool, optional
            Unused flag for API compatibility.
        """

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        moves = list(board.legal_moves)
        if not moves:
            return None, 0.0
        move = random.choice(moves)
        tmp = board.copy(stack=False)
        tmp.push(move)
        conf = evaluator.position_score(tmp, self.color)
        if context is not None and context.mobility != 0:
            conf += MOBILITY_FACTOR if context.mobility > 0 else -MOBILITY_FACTOR
        return move, float(conf)