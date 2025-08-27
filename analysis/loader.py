from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import csv
from typing import Any, Dict, List, Optional

import chess

try:
    # rpy2 is optional; only needed for RDS export
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    RPY2_AVAILABLE = True
except Exception:  # pragma: no cover - rpy2 may be missing in tests
    RPY2_AVAILABLE = False

REQUIRED_KEYS = {"moves", "fens", "modules_w", "modules_b"}


def load_runs(path: str) -> List[Dict[str, Any]]:
    """Load run JSON files from *path* and include save timestamps.

    Each JSON file must contain the keys defined in :data:`REQUIRED_KEYS`.
    The returned run dictionaries additionally include a ``date`` field with
    the file's modification time encoded via :meth:`datetime.isoformat`.
    """
    runs: List[Dict[str, Any]] = []
    base_path = Path(path)

    for file in sorted(base_path.glob("*.json")):
        with file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(
                f"Missing keys in {file.name}: {', '.join(sorted(missing))}"
            )

        runs.append(
            {
                "game_id": file.stem,
                "moves": data["moves"],
                "fens": data["fens"],
                "modules_w": data["modules_w"],
                "modules_b": data["modules_b"],
                "result": data.get("result"),
                "date": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
            }
        )

    return runs


def export_move_table(
    path: str,
    csv_path: Optional[str] = None,
    rds_path: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Extract per-move piece and destination square information.

    Parameters
    ----------
    path:
        Directory containing run JSON files.
    csv_path, rds_path:
        Optional output paths.  When provided the extracted table is written
        either as a CSV file or an RDS file.  Exporting to RDS requires
        :mod:`rpy2` to be installed.

    Returns
    -------
    List[Dict[str, str]]
        A list of ``{"game_id", "piece", "to"}`` dictionaries for every move
        in *path*.
    """

    runs = load_runs(path)
    records: List[Dict[str, str]] = []

    for run in runs:
        board = chess.Board()
        for mv in run["moves"]:
            move = chess.Move.from_uci(mv)
            piece = board.piece_at(move.from_square)
            if piece is None:
                board.push(move)
                continue
            board.push(move)
            records.append(
                {
                    "game_id": run["game_id"],
                    "piece": chess.piece_name(piece.piece_type),
                    "to": chess.square_name(move.to_square),
                }
            )

    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["game_id", "piece", "to"])
            writer.writeheader()
            writer.writerows(records)

    if rds_path:
        if not RPY2_AVAILABLE:
            raise RuntimeError("rpy2 is required for RDS export")

        pandas2ri.activate()
        columns = {
            "game_id": robjects.StrVector([r["game_id"] for r in records]),
            "piece": robjects.StrVector([r["piece"] for r in records]),
            "to": robjects.StrVector([r["to"] for r in records]),
        }
        df = robjects.DataFrame(columns)
        robjects.r["saveRDS"](df, rds_path)

    return records


if __name__ == "__main__":  # pragma: no cover - CLI utility
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert run JSON files into per-move tables"
    )
    parser.add_argument("path", help="Directory containing run JSON files")
    parser.add_argument("--csv", dest="csv_path", help="Output CSV path")
    parser.add_argument("--rds", dest="rds_path", help="Output RDS path")
    args = parser.parse_args()

    export_move_table(args.path, csv_path=args.csv_path, rds_path=args.rds_path)
