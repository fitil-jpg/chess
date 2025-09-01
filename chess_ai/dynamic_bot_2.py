import logging
logger = logging.getLogger(__name__)

from core.evaluator import Evaluator
from chess_ai.utility_bot import UtilityBot
from chess_ai.chess_bot import ChessBot   # твій основний бот
from chess_ai.endgame_bot import EndgameBot
from chess_ai.random_bot import RandomBot
from utils import GameContext
import chess


_SHARED_EVALUATOR: Evaluator | None = None

class DynamicBot2:
    """
    Бот, який обирає іншого агента залежно від features (ознаки позиції).
    Якщо є підвішена — UtilityBot, якщо можна дати шах — ChessBot, якщо endgame — EndgameBot, інакше RandomBot.
    """
    def __init__(self, color):
        self.color = color
        self.utility_bot = UtilityBot(color)
        self.chess_bot = ChessBot(color)      # Замість CenterBot
        self.endgame_bot = EndgameBot(color)
        self.random_bot = RandomBot(color)
        # Можна додавати ще агентів тут

    def choose_move(
        self,
        board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = True,
    ):
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)
        features = evaluator.compute_features(self.color)

        if features["has_hanging_enemy"]:
            move, reason = self.utility_bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
            bot_name = "UtilityBot"
        elif features["can_give_check"]:
            move, reason = self.chess_bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
            bot_name = "ChessBot"
        elif self.is_endgame(board):
            move, reason = self.endgame_bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
            bot_name = "EndgameBot"
        else:
            move, reason = self.random_bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
            bot_name = "RandomBot"

        debug_info = {
            "bot": bot_name,
            "reason": reason,
            "features": features
        }
        return (move, debug_info) if debug else move

    def is_endgame(self, board):
        # Дуже просте правило: залишилось <= 5 не-пішаків на дошці
        non_pawns = sum(1 for sq in chess.SQUARES
                        if board.piece_at(sq) and board.piece_at(sq).piece_type != chess.PAWN)
        return non_pawns <= 5