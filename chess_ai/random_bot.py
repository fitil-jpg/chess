import random

from core.utils import GameContext
from core.evaluator import Evaluator


class RandomBot:
    def __init__(self, color: bool):
        self.color = color

    def choose_move(
        self,
        board,
        ctx: GameContext,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return a random legal move adjusted by position evaluation."""

        evaluator = evaluator or Evaluator(board)

        moves = list(board.legal_moves)
        if not moves:
            return None, 0.0
        move = random.choice(moves)
        tmp = board.copy(stack=False)
        tmp.push(move)
        conf = evaluator.position_score(tmp, self.color)
        return move, float(conf)
