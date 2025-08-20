import chess
import pytest

from metrics import MetricsManager as PublicMetricsManager
from core.metrics import MetricsManager as CoreMetricsManager


@pytest.fixture(params=[PublicMetricsManager, CoreMetricsManager])
def manager_cls(request):
    return request.param


def test_count_attacked_squares(manager_cls):
    board = chess.Board("4k3/8/8/8/3Q4/8/8/4K3 w - - 0 1")
    mm = manager_cls(board)
    assert mm.count_attacked_squares() == 24


def test_count_defended_pieces(manager_cls):
    board = chess.Board("8/p7/8/8/4P3/3P4/8/4K3 w - - 0 1")
    mm = manager_cls(board)
    assert mm.count_defended_pieces() == 1


def test_evaluate_center_control(manager_cls):
    board = chess.Board("4k3/8/8/8/8/2N5/8/4K3 w - - 0 1")
    mm = manager_cls(board)
    assert mm.evaluate_center_control() == 2


def test_evaluate_king_safety(manager_cls):
    board = chess.Board("6k1/4r3/8/8/8/8/8/4K3 w - - 0 1")
    mm = manager_cls(board)
    assert mm.evaluate_king_safety() == -1


def test_evaluate_pawn_structure(manager_cls):
    board = chess.Board("8/8/8/8/8/P7/P7/4K3 w - - 0 1")
    mm = manager_cls(board)
    assert mm.evaluate_pawn_structure() == -1

