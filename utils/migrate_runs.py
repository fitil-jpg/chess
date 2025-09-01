from __future__ import annotations

"""Add missing results to run JSON files.

The script scans a directory for ``*.json`` files produced by ``main.py`` and
ensures that each contains a ``result`` field.  When the field is absent or
set to the placeholder ``"*"``, the final game outcome is reconstructed either
from the last FEN string or by replaying the recorded SAN moves.

Usage
-----
    python utils/migrate_runs.py --runs runs/
"""

from utils.usage_logger import record_usage

record_usage(__file__)

import argparse
import json
from pathlib import Path
from typing import Any

import chess

DEFAULT_RESULT = "*"


def _derive_result(data: dict[str, Any]) -> str:
    """Return the game result for a run dictionary."""

    if data.get("fens"):
        board = chess.Board(data["fens"][-1])
    else:
        board = chess.Board()
        for san in data.get("moves", []):
            board.push_san(san)

    if not board.is_game_over(claim_draw=True):
        raise ValueError("Game is not finished")

    return board.result(claim_draw=True)


def migrate_runs(path: str) -> None:
    """Update run JSON files in *path* with a missing ``result`` field."""

    base = Path(path)
    for file in sorted(base.glob("*.json")):
        with file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        result = data.get("result")
        if result not in (None, DEFAULT_RESULT):
            continue

        try:
            data["result"] = _derive_result(data)
        except ValueError as exc:
            print(f"Skipping {file.name}: {exc}")
            continue

        with file.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print(f"Updated {file.name} -> {data['result']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs", default="runs/", help="Directory containing run JSON files"
    )
    args = parser.parse_args(argv)

    migrate_runs(args.runs)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
