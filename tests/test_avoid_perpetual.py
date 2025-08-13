import chess
from chess_ai.chess_bot import ChessBot
from chess_ai.dynamic_bot import DynamicBot
from core.evaluator import Evaluator


def _repetition_board():
    board = chess.Board('k6r/5NQ1/8/8/8/8/8/K7 w - - 0 1')
    board.push(chess.Move.from_uci('g7g8'))
    board.push(chess.Move.from_uci('a8a7'))
    board.push(chess.Move.from_uci('g8g7'))
    board.push(chess.Move.from_uci('a7a8'))
    assert board.is_repetition(2)
    return board


def test_chess_bot_takes_rook_over_check():
    board = _repetition_board()
    bot = ChessBot(chess.WHITE)
    evaluator = Evaluator(board)
    move, conf = bot.choose_move(board, evaluator)
    assert move == chess.Move.from_uci('f7h8')


def test_dynamic_bot_takes_rook_over_check():
    board = _repetition_board()
    bot = DynamicBot(chess.WHITE)
    evaluator = Evaluator(board)
    move, conf = bot.choose_move(board, evaluator, debug=False)
    assert move == chess.Move.from_uci('f7h8')
