import time
import chess
import types

from scripts import tournament as T


class LegalBot:
    def __init__(self, color: bool):
        self.color = color
    def choose_move(self, board: chess.Board):
        try:
            return next(iter(board.legal_moves))
        except StopIteration:
            return None


class IllegalBot:
    def __init__(self, color: bool):
        self.color = color
    def choose_move(self, board: chess.Board):
        # Return a syntactically valid but illegal move from the start
        # (rook from a1 to a8 is blocked by own pieces at game start)
        return chess.Move.from_uci("a1a8")


class CrashBot:
    def __init__(self, color: bool):
        self.color = color
    def choose_move(self, board: chess.Board):
        raise ValueError("boom")


class TimeoutBot:
    def __init__(self, color: bool, delay: float = 0.2):
        self.color = color
        self.delay = delay
    def choose_move(self, board: chess.Board):
        time.sleep(self.delay)
        return next(iter(board.legal_moves), None)


def _stub_factory(name: str):
    def factory(color: bool):
        if name == "IllegalBot":
            return IllegalBot(color)
        if name == "CrashBot":
            return CrashBot(color)
        if name == "TimeoutBot":
            return TimeoutBot(color, delay=0.2)
        return LegalBot(color)
    return factory


def test_illegal_move_forfeits_with_reason(monkeypatch):
    # Patch make_agent inside the tournament module
    def make_agent(name: str, color: bool):
        return _stub_factory(name)(color)
    monkeypatch.setattr(T, "make_agent", make_agent)

    res = T.play_single_game("IllegalBot", "LegalBot", max_plies=2)
    assert res == "0-1"
    assert T.LAST_GAME_META is not None
    assert T.LAST_GAME_META.get("kind") == "illegal_move"
    assert T.LAST_GAME_META.get("side") == "white"
    assert T.LAST_GAME_META.get("agent") == "IllegalBot"


def test_crash_counts_as_loss_and_captures_error(monkeypatch):
    def make_agent(name: str, color: bool):
        return _stub_factory(name)(color)
    monkeypatch.setattr(T, "make_agent", make_agent)

    res = T.play_single_game("CrashBot", "LegalBot", max_plies=2, time_per_move=1)
    assert res == "0-1"
    assert T.LAST_GAME_META is not None
    assert T.LAST_GAME_META.get("kind") == "agent_error"
    assert T.LAST_GAME_META.get("side") == "white"
    assert T.LAST_GAME_META.get("agent") == "CrashBot"
    err = str(T.LAST_GAME_META.get("error"))
    assert "ValueError" in err or "boom" in err


def test_timeout_flag_fall_forfeits_with_metadata(monkeypatch):
    def make_agent(name: str, color: bool):
        return _stub_factory(name)(color)
    monkeypatch.setattr(T, "make_agent", make_agent)

    res = T.play_single_game(
        "TimeoutBot", "LegalBot", max_plies=2, clock_initial=0.0001, clock_increment=0.0
    )
    assert res == "0-1"
    assert T.LAST_GAME_META is not None
    assert T.LAST_GAME_META.get("kind") == "timeout"
    assert T.LAST_GAME_META.get("side") == "white"
    assert T.LAST_GAME_META.get("agent") == "TimeoutBot"
