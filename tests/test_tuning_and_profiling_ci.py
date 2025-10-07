import os
import time

import chess

from core.evaluator import Evaluator
from chess_ai.scorer import Scorer


def test_scorer_env_override_affects_score(monkeypatch):
    # Ensure different weight changes the score of a crafted feature map
    monkeypatch.setenv("CHESS_SCORER_CAPTURE_DEFENDED", "1000")
    s = Scorer()
    hi = s.score({"is_capture": True})
    monkeypatch.setenv("CHESS_SCORER_CAPTURE_DEFENDED", "1")
    s2 = Scorer()
    lo = s2.score({"is_capture": True})
    assert hi > lo


def test_evaluator_env_overrides_penalties(monkeypatch):
    b = chess.Board()
    monkeypatch.setenv("CHESS_EVAL_ISOLATED_PENALTY", "-30")
    ev = Evaluator(b)
    assert ev.isolated_penalty == -30
    monkeypatch.setenv("CHESS_EVAL_PASSED_BONUS", "50")
    ev2 = Evaluator(b)
    assert ev2.passed_bonus == 50


def test_mobility_speed_budget():
    # Crude speed budget: 1000 mobility evaluations should be fast enough on CI
    b = chess.Board()
    ev = Evaluator(b)
    t0 = time.time()
    total = 0
    for _ in range(1000):
        w, bl = ev.mobility(b)
        total += (w + bl)
    dt = time.time() - t0
    # Budget: < 0.7s on CI machines; relax if flaking
    assert dt < 0.7, f"mobility too slow: {dt:.3f}s; total={total}"

