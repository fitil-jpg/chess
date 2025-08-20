"""Tests for the optional R evaluation bridge."""

import importlib
import sys
import warnings

import chess
import pytest


def test_import_without_r_no_warning(monkeypatch):
    """Importing r_bridge without rpy2 should not emit warnings."""
    monkeypatch.setitem(sys.modules, "rpy2", None)
    sys.modules.pop("chess_ai.hybrid_bot.r_bridge", None)
    with warnings.catch_warnings(record=True) as caught:
        rb = importlib.import_module("chess_ai.hybrid_bot.r_bridge")
    assert caught == []
    with pytest.raises(RuntimeError):
        rb.eval_board(chess.Board())


def test_orchestrator_falls_back(monkeypatch):
    """HybridOrchestrator should fall back to Python eval when R is disabled."""
    monkeypatch.delenv("CHESS_USE_R", raising=False)
    import chess_ai.hybrid_bot.orchestrator as orch
    importlib.reload(orch)
    monkeypatch.setattr(orch, "evaluate_position", lambda b: 42.0)
    o = orch.HybridOrchestrator(chess.WHITE)
    assert o._r_eval(chess.Board()) == 42.0


def test_eval_board_returns_float_when_r_available():
    """If rpy2 is present the bridge should return a float score."""
    pytest.importorskip("rpy2")
    import chess_ai.hybrid_bot.r_bridge as rb
    importlib.reload(rb)
    score = rb.eval_board(chess.Board())
    assert isinstance(score, float)

