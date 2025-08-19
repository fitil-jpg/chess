import chess
import pytest

rpy2 = pytest.importorskip("rpy2")

from chess_ai.hybrid_bot.r_bridge import eval_board


def test_eval_board_returns_float():
    board = chess.Board()
    score = eval_board(board)
    assert isinstance(score, float)
