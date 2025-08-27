from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import csv
import random
from collections import Counter
from typing import Any, Dict, Iterator, List, Optional

import chess

try:
    # rpy2 is optional; only needed for RDS export
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    RPY2_AVAILABLE = True
except Exception:  # pragma: no cover - rpy2 may be missing in tests
    RPY2_AVAILABLE = False

REQUIRED_KEYS = {"moves", "fens", "modules_w", "modules_b"}


def iter_runs(
    path: str,
    limit: Optional[int] = None,
    seed: Optional[int] = None,
) -> Iterator[Dict[str, Any]]:
    """Yield run dictionaries from *path* one by one.

    Parameters
    ----------
    path:
        Directory holding run ``.json`` files.
    limit, seed:
        Optional sampling parameters.  When *limit* is given, at most this many
        runs are processed.  If *seed* is provided the file order is shuffled
        deterministically before applying the limit.

    Yields
    ------
    Dict[str, Any]
        Run dictionaries with the required fields plus a ``date`` timestamp
        derived from the file's modification time.
    """

    base_path = Path(path)
    files = sorted(base_path.glob("*.json"))

    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(files)

    if limit is not None:
        files = files[:limit]

    for file in files:
        with file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(
                f"Missing keys in {file.name}: {', '.join(sorted(missing))}"
            )

        yield {
            "game_id": file.stem,
            "moves": data["moves"],
            "fens": data["fens"],
            "modules_w": data["modules_w"],
            "modules_b": data["modules_b"],
            "result": data.get("result"),
            "date": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
        }


def aggregate_stats(
    path: str, limit: Optional[int] = None, seed: Optional[int] = None
) -> Dict[str, Any]:
    """Aggregate basic statistics across run files in *path*.

    The function processes run JSON files one at a time, keeping only the
    accumulated statistics in memory.  It counts how many games and moves were
    processed and aggregates module usage across both colours.
    """

    module_counts: Counter[str] = Counter()
    total_moves = 0
    total_games = 0

    for run in iter_runs(path, limit=limit, seed=seed):
        total_games += 1
        total_moves += len(run["moves"])
        module_counts.update(run.get("modules_w", []))
        module_counts.update(run.get("modules_b", []))

    return {
        "games": total_games,
        "moves": total_moves,
        "module_usage": dict(module_counts),
    }


def export_move_table(
    path: str,
    csv_path: Optional[str] = None,
    rds_path: Optional[str] = None,
    limit: Optional[int] = None,
    seed: Optional[int] = None,
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
    limit, seed:
        Optional sampling parameters forwarded to :func:`iter_runs`.

    Returns
    -------
    List[Dict[str, str]]
        A list of ``{"game_id", "piece", "to"}`` dictionaries for every move
        in *path*.
    """

    records: List[Dict[str, str]] = []

    for run in iter_runs(path, limit=limit, seed=seed):
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
    parser.add_argument(
        "--sample-size",
        type=int,
        dest="sample_size",
        help="Randomly sample at most this many runs",
    )
    parser.add_argument(
        "--seed", type=int, dest="seed", help="Seed for random sampling"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print aggregated statistics instead of move table",
    )
    args = parser.parse_args()

    if args.stats:
        stats = aggregate_stats(args.path, limit=args.sample_size, seed=args.seed)
        print(json.dumps(stats))
    else:
        export_move_table(
            args.path,
            csv_path=args.csv_path,
            rds_path=args.rds_path,
            limit=args.sample_size,
            seed=args.seed,
        )
