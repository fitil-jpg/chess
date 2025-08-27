"""Tests for optional R integration in :mod:`chess_ai.dynamic_bot`."""

import importlib

import pytest

chess = pytest.importorskip("chess")


def test_dynamic_bot_uses_r_agent(monkeypatch):
    """DynamicBot should consider the R evaluator when enabled."""

    monkeypatch.setenv("CHESS_USE_R", "1")
    import chess_ai.dynamic_bot as db
    importlib.reload(db)

    def fake_eval(board: chess.Board) -> float:
        last = board.peek().uci()
        return 5.0 if last == "e2e4" else 0.0

    monkeypatch.setattr(db, "_r_eval_board", fake_eval)

    weights = {
        "aggressive": 0.0,
        "fortify": 0.0,
        "critical": 0.0,
        "endgame": 0.0,
        "random": 0.0,
        "center": 0.0,
        "neural": 0.0,
        "r": 1.0,
    }

    bot = db.DynamicBot(chess.WHITE, weights=weights, use_r=True)
    board = chess.Board()
    move, score = bot.choose_move(board)

    assert move == chess.Move.from_uci("e2e4")
    assert score == 5.0

