"""Regression tests for the top-level evaluator's terminal handling."""

import pytest

chess = pytest.importorskip("chess")

from evaluation import MATE_SCORE, evaluate


def test_evaluate_reports_positive_mate_score_when_black_is_mated():
    board = chess.Board("7k/7Q/7K/8/8/8/8/8 b - - 0 1")
    assert board.is_checkmate()

    score, details = evaluate(board)

    assert score == MATE_SCORE
    assert details["total"] == score


def test_evaluate_reports_negative_mate_score_when_white_is_mated():
    board = chess.Board("7K/7q/7k/8/8/8/8/8 w - - 0 1")
    assert board.is_checkmate()

    score, details = evaluate(board)

    assert score == -MATE_SCORE
    assert details["total"] == score


def test_evaluate_reports_draw_for_stalemate():
    board = chess.Board("7k/8/6QK/8/8/8/8/8 b - - 0 1")
    assert board.is_stalemate()

    score, details = evaluate(board)

    assert score == 0
    assert details["total"] == 0
