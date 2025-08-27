import chess

from core.evaluator import Evaluator
from chess_ai.dynamic_bot import DynamicBot


def test_knight_two_move_fork_detected_and_neutralised():
    board = chess.Board("6k1/8/8/6n1/8/5N2/4K3/3Q4 w - - 0 1")
    evaluator = Evaluator(board)
    critical = evaluator.criticality(board, chess.WHITE)
    assert critical and critical[0][0] == chess.G5

    bot = DynamicBot(chess.WHITE)
    move, score = bot.choose_move(board, evaluator=evaluator)
    assert move == chess.Move.from_uci("f3g5")
