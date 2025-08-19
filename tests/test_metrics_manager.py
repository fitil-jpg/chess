import chess

from metrics import MetricsManager


def test_count_attacked_squares():
    board = chess.Board("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1")
    mm = MetricsManager(board)
    assert mm.count_attacked_squares() == 24


def test_count_defended_pieces():
    board = chess.Board("8/p7/8/8/4P3/3P4/8/4K3 w - - 0 1")
    mm = MetricsManager(board)
    assert mm.count_defended_pieces() == 1


def test_evaluate_center_control():
    board = chess.Board("4k3/8/8/8/8/2N5/8/4K3 w - - 0 1")
    mm = MetricsManager(board)
    assert mm.evaluate_center_control() == 2


def test_evaluate_king_safety():
    board = chess.Board("6k1/4r3/8/8/8/8/8/4K3 w - - 0 1")
    mm = MetricsManager(board)
    assert mm.evaluate_king_safety() == -1


def test_evaluate_pawn_structure():
    board = chess.Board("8/8/8/8/8/P7/P7/4K3 w - - 0 1")
    mm = MetricsManager(board)
    assert mm.evaluate_pawn_structure() == -1

