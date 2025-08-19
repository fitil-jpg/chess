import random
import chess

from chess_ai.random_bot import RandomBot, MOBILITY_FACTOR


def test_random_bot_mobility_bias(context, evaluator):
    board = chess.Board()
    evaluator.board = board
    bot = RandomBot(chess.WHITE)

    random.seed(0)
    context.mobility = 5
    _, conf_pos = bot.choose_move(board, context=context, evaluator=evaluator)

    random.seed(0)
    context.mobility = -5
    _, conf_neg = bot.choose_move(board, context=context, evaluator=evaluator)

    assert conf_pos - conf_neg == 2 * MOBILITY_FACTOR
