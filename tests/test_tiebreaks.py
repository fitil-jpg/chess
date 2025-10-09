from __future__ import annotations

import sys
import types
import runpy

import chess


class _StubAgent:
    def __init__(self, color: bool):
        self.color = color

    def choose_move(self, board: chess.Board):
        # Always play the first legal move quickly
        for m in board.legal_moves:
            return m
        return None


def _install_stub_bot_agent() -> None:
    # Create a fake chess_ai package and bot_agent submodule before loading the script
    pkg = types.ModuleType("chess_ai")
    bot_agent = types.ModuleType("chess_ai.bot_agent")

    def make_agent(name: str, color: bool):
        return _StubAgent(color)

    def get_agent_names():
        return ["StubA", "StubB"]

    bot_agent.make_agent = make_agent  # type: ignore[attr-defined]
    bot_agent.get_agent_names = get_agent_names  # type: ignore[attr-defined]

    sys.modules.setdefault("chess_ai", pkg)
    sys.modules["chess_ai.bot_agent"] = bot_agent


def _load_tournament_module():
    # Ensure stub is installed before importing the script
    _install_stub_bot_agent()
    mod_globals = runpy.run_path("scripts/tournament.py", run_name="__not_main__")
    return mod_globals


def test_tiebreaks_two_blitz_then_armageddon_draw_odds_black():
    mod = _load_tournament_module()

    play_series = mod["play_series"]

    # Force quick draws by limiting plies; tie-breaks enabled; main time control irrelevant here
    a, b = "StubA", "StubB"
    pts_a, pts_b, results = play_series(
        a,
        b,
        series_games=3,           # Best-of-3 to ensure odd series (tie-break eligible)
        max_plies=2,              # Low cap to produce draws quickly
        time_main=60.0,
        increment=0.0,
        enable_tiebreaks=True,
    )

    # Expect 3 (main) + 2 (blitz) + 1 (Armageddon) = 6 games recorded
    assert len(results) == 6

    # All games should be recorded; Armageddon result can be a draw string, but draw odds
    # must award the match to Black for scoring purposes.
    # With 5 draws before Armageddon, the next game index is 5 (0-based), so White=B, Black=A.
    # Therefore side 'a' should receive the Armageddon point on draw.
    assert pts_a == 3.5 and pts_b == 2.5

    # Sanity: ensure at least the last game is a legal chess result string
    assert results[-1] in {"1-0", "0-1", "1/2-1/2"}
