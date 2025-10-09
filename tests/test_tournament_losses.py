import importlib.util
import os
import time

import chess
import pytest


def import_tournament_module():
    # Import scripts/tournament.py as a module
    here = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(here, "scripts", "tournament.py")
    spec = importlib.util.spec_from_file_location("_tournament", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    return mod


def test_illegal_move_counts_as_loss(monkeypatch):
    mod = import_tournament_module()

    class IllegalAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            # From the initial position, a rook move from a1 is illegal
            return chess.Move.from_uci("a1a3")

    class SafeAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            # Return a legal move quickly
            return chess.Move.from_uci("e7e5") if board.turn == chess.BLACK else chess.Move.from_uci("e2e4")

    def fake_make_agent(name: str, color: bool):
        return IllegalAgent(color) if name == "ILLEGAL" else SafeAgent(color)

    monkeypatch.setattr(mod, "make_agent", fake_make_agent)

    res = mod.play_single_game("ILLEGAL", "SAFE", max_plies=4)
    assert res == "0-1"  # White starts and loses on illegal move


def test_crash_counts_as_loss(monkeypatch):
    mod = import_tournament_module()

    class CrashAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            raise RuntimeError("boom")

    class SafeAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            return chess.Move.from_uci("e7e5") if board.turn == chess.BLACK else chess.Move.from_uci("e2e4")

    def fake_make_agent(name: str, color: bool):
        return CrashAgent(color) if name == "CRASH" else SafeAgent(color)

    monkeypatch.setattr(mod, "make_agent", fake_make_agent)

    res = mod.play_single_game("CRASH", "SAFE", max_plies=4)
    assert res == "0-1"  # White crashes on move selection


def test_timeout_counts_as_loss(monkeypatch):
    mod = import_tournament_module()

    class SlowAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            time.sleep(0.05)
            return chess.Move.from_uci("e2e4")

    class SafeAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            return chess.Move.from_uci("e7e5") if board.turn == chess.BLACK else chess.Move.from_uci("e2e4")

    def fake_make_agent(name: str, color: bool):
        return SlowAgent(color) if name == "SLOW" else SafeAgent(color)

    monkeypatch.setenv("CHESS_MOVE_TIME_LIMIT_S", "0.01")
    monkeypatch.setattr(mod, "make_agent", fake_make_agent)

    res = mod.play_single_game("SLOW", "SAFE", max_plies=4)
    assert res == "0-1"  # White exceeds per-move time limit


def test_none_move_counts_as_loss(monkeypatch):
    mod = import_tournament_module()

    class NoneAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            return None

    class SafeAgent:
        def __init__(self, _color):
            self._color = _color
        def choose_move(self, board: chess.Board):
            return chess.Move.from_uci("e7e5") if board.turn == chess.BLACK else chess.Move.from_uci("e2e4")

    def fake_make_agent(name: str, color: bool):
        return NoneAgent(color) if name == "NONE" else SafeAgent(color)

    monkeypatch.setattr(mod, "make_agent", fake_make_agent)

    res = mod.play_single_game("NONE", "SAFE", max_plies=4)
    assert res == "0-1"  # White returns no move
