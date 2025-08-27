import pytest

chess = pytest.importorskip("chess")
if not hasattr(chess, "Board"):
    pytest.skip("python-chess not installed", allow_module_level=True)

from core.evaluator import escape_squares


def _moves_to_squares(moves):
    return {m.to_square for m in moves}


def test_escape_squares_one_escape():
    board = chess.Board("n5k1/1B42/8/P7/8/8/8/7K w - - 0 1")
    escapes = escape_squares(board, chess.A8)
    assert _moves_to_squares(escapes) == {chess.C7}


def test_escape_squares_two_escapes():
    board = chess.Board("n5k1/1B42/8/8/8/8/8/7K w - - 0 1")
    escapes = escape_squares(board, chess.A8)
    assert _moves_to_squares(escapes) == {chess.B6, chess.C7}
