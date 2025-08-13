from core.utils import GameContext
from core.evaluator import Evaluator

from .chess_bot import ChessBot
from .endgame_bot import EndgameBot
from .random_bot import RandomBot
from .aggressive_bot import AggressiveBot
from .fortify_bot import FortifyBot


class DynamicBot:
    """Meta-agent that gathers suggestions from all sub-bots.

    Each sub-bot returns ``(move, confidence)``.  DynamicBot simply chooses the
    move with the highest reported confidence.
    """

    def __init__(self, color: bool):
        self.color = color
        self.agents = [
            AggressiveBot(color),
            FortifyBot(color),
            EndgameBot(color),
            RandomBot(color),
            ChessBot(color),
        ]

    def choose_move(
        self,
        board,
        ctx: GameContext,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        evaluator = evaluator or Evaluator(board)
        proposals = []
        for agent in self.agents:
            move, conf = agent.choose_move(board, ctx, evaluator)
            if move is not None:
                proposals.append((conf, move))

        if not proposals:
            return None, 0.0

        conf, move = max(proposals, key=lambda x: x[0])
        if debug:
            print(f"DynamicBot selected {move} with confidence {conf}")
        return move, conf
