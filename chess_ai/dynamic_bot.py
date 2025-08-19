from .chess_bot import ChessBot
from .endgame_bot import EndgameBot
from .random_bot import RandomBot
from .aggressive_bot import AggressiveBot
from .fortify_bot import FortifyBot
from core.evaluator import Evaluator
from utils import GameContext


_SHARED_EVALUATOR: Evaluator | None = None


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
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Gather candidate moves from each sub-bot and choose the best."""

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        proposals = []
        for agent in self.agents:
            move, conf = agent.choose_move(board, context=context, evaluator=evaluator)
            if move is not None:
                proposals.append((conf, move))

        if not proposals:
            return None, 0.0

        conf, move = max(proposals, key=lambda x: x[0])
        if debug:
            print(f"DynamicBot selected {move} with confidence {conf}")
        return move, conf
