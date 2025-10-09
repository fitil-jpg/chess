from __future__ import annotations

import json
from pathlib import Path

from scripts.tournament import seed_agents_from_latest_elo


def _write_elo(path: Path, ratings: dict[str, float]) -> None:
    payload = {
        "schema_version": 1,
        "task": "selfplay_elo",
        "timestamp": path.stem.split("selfplay_elo_")[-1],
        "agents": list(ratings.keys()),
        "k_factor": 24.0,
        "ratings": ratings,
        "games": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


essential_agents = [
    "DynamicBot",
    "AggressiveBot",
    "FortifyBot",
    "EndgameBot",
    "CriticalBot",
    "KingValueBot",
    "TrapBot",
    "RandomBot",
]


def test_seed_agents_from_latest_elo_orders_by_desc_rating_and_name(tmp_path):
    # Older file
    p1 = tmp_path / "selfplay_elo_20240101_000000.json"
    _write_elo(p1, {"A": 1400.0, "B": 1600.0})

    # Newer file (should be selected)
    p2 = tmp_path / "selfplay_elo_20240301_010101.json"
    _write_elo(p2, {"AggressiveBot": 1600.0, "FortifyBot": 1400.0})

    agents = ["FortifyBot", "RandomBot", "AggressiveBot"]
    ordered, source = seed_agents_from_latest_elo(agents, str(tmp_path))

    # Should pick p2 as source
    assert source is not None and source.endswith(p2.name)

    # Ratings: AggressiveBot=1600, RandomBot=1500(default), FortifyBot=1400
    assert ordered == ["AggressiveBot", "RandomBot", "FortifyBot"]


def test_seed_agents_from_latest_elo_no_files_keeps_order(tmp_path):
    agents = ["X", "Y"]
    ordered, source = seed_agents_from_latest_elo(agents, str(tmp_path))
    assert source is None
    assert ordered == agents
