import random
import chess

from chess_ai.random_bot import RandomBot, MOBILITY_FACTOR
from utils import GameContext


def test_random_bot_mobility_bias():
    board = chess.Board()
    bot = RandomBot(chess.WHITE)

    random.seed(0)
    _, conf_pos = bot.choose_move(
        board, GameContext(mobility=5)
    )
    random.seed(0)
    _, conf_neg = bot.choose_move(
        board, GameContext(mobility=-5)
    )

    assert conf_pos - conf_neg == 2 * MOBILITY_FACTOR
