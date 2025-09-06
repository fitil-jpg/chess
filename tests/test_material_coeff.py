import pytest

chess = pytest.importorskip("chess")

from scripts.material_coeff import coefficient_r, average_strength


def test_initial_position():
    board = chess.Board()
    assert coefficient_r(board) == 0
    assert average_strength(board, chess.WHITE) == pytest.approx(2.6)
    assert average_strength(board, chess.BLACK) == pytest.approx(2.6)


def test_simple_endgame_position():
    board = chess.Board("8/2p5/3p4/3P4/2P5/6K1/8/6k1 w - - 0 47")
    assert coefficient_r(board) == 0
    assert average_strength(board, chess.WHITE) == 1
    assert average_strength(board, chess.BLACK) == 1
