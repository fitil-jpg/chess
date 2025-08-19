import pytest

import chess

from metrics import MetricsManager as MainMetrics
from core.metrics import MetricsManager as CoreMetrics


@pytest.mark.parametrize("manager_cls", [MainMetrics, CoreMetrics])
def test_count_attacked_squares(manager_cls):
    board = chess.Board("8/8/8/8/8/8/8/R7 w - - 0 1")
    metrics = manager_cls(board)
    assert metrics.count_attacked_squares() == 14


@pytest.mark.parametrize("manager_cls", [MainMetrics, CoreMetrics])
def test_count_defended_pieces(manager_cls):
    board = chess.Board("8/8/8/8/8/8/4R3/4K3 w - - 0 1")
    metrics = manager_cls(board)
    assert metrics.count_defended_pieces() == 2


@pytest.mark.parametrize("manager_cls", [MainMetrics, CoreMetrics])
def test_evaluate_center_control(manager_cls):
    board = chess.Board("8/8/8/8/8/5N2/8/8 w - - 0 1")
    metrics = manager_cls(board)
    assert metrics.evaluate_center_control() == 2


@pytest.mark.parametrize("manager_cls", [MainMetrics, CoreMetrics])
def test_evaluate_king_safety(manager_cls):
    board = chess.Board("8/8/8/8/4K3/8/8/8 w - - 0 1")
    metrics = manager_cls(board)
    assert metrics.evaluate_king_safety() == 8


@pytest.mark.parametrize("manager_cls", [MainMetrics, CoreMetrics])
def test_evaluate_pawn_structure(manager_cls):
    board = chess.Board("8/8/8/8/8/8/P1P5/8 w - - 0 1")
    metrics = manager_cls(board)
    assert metrics.evaluate_pawn_structure() == -2

