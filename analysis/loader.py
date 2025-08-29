from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
import csv
import random
from typing import Any, Dict, Iterable, Iterator, List, Optional

import chess
from scenarios import detect_scenarios

try:
    # rpy2 is optional; only needed for RDS export
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    RPY2_AVAILABLE = True
except Exception:  # pragma: no cover - rpy2 may be missing in tests
    RPY2_AVAILABLE = False

REQUIRED_KEYS = {"moves", "fens", "modules_w", "modules_b"}


def stream_runs(
    path: str, sample_size: Optional[int] = None, seed: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """Yield run dictionaries from *path* one by one.

    Parameters
    ----------
    path:
        Directory containing run JSON files.
    sample_size, seed:
        Optional sampling parameters.  When *sample_size* is provided, a
        deterministic subset of files is chosen using *seed*.

    Yields
    ------
    Dict[str, Any]
        Run dictionaries containing the required fields plus ``game_id`` and
        ``date``.
    """

    base_path = Path(path)
    files = sorted(base_path.glob("*.json"))

    if sample_size is not None and sample_size < len(files):
        rng = random.Random(seed)
        files = rng.sample(files, sample_size)

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


def load_runs(path: str) -> List[Dict[str, Any]]:
    """Load run JSON files from *path*.

    This helper materializes :func:`stream_runs` into a list for
    compatibility with existing callers.
    """

    return list(stream_runs(path))


def aggregate_run_stats(
    path: str, sample_size: Optional[int] = None, seed: Optional[int] = None
) -> Dict[str, int]:
    """Aggregate basic statistics from run files in *path*.

    Statistics include the number of games and total moves processed.
    The calculation streams files one by one to avoid loading all runs into
    memory.
    """

    stats = {"games": 0, "moves": 0}
    for run in stream_runs(path, sample_size=sample_size, seed=seed):
        stats["games"] += 1
        stats["moves"] += len(run["moves"])
    return stats


def export_move_table(
    path: str,
    csv_path: Optional[str] = None,
    rds_path: Optional[str] = None,
    *,
    sample_size: Optional[int] = None,
    seed: Optional[int] = None,
) -> tuple[List[Dict[str, str]], Dict[str, int]]:
    """Extract per-move piece and destination square information.

    Parameters
    ----------
    path:
        Directory containing run JSON files.
    csv_path, rds_path:
        Optional output paths.  When provided the extracted table is written
        either as a CSV file or an RDS file.  Exporting to RDS requires
        :mod:`rpy2` to be installed.
    sample_size, seed:
        Limit the number of games processed and control the randomness of the
        selection.

    Returns
    -------
    tuple[List[Dict[str, str]], Dict[str, int]]
        The per-move records and basic statistics collected during parsing.
    """

    records: List[Dict[str, str]] = []
    stats = {"games": 0, "moves": 0}

    for run in stream_runs(path, sample_size=sample_size, seed=seed):
        stats["games"] += 1
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
            stats["moves"] += 1

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

    # Stats are primarily for CLI output; callers may ignore them.
    return records, stats


def export_fen_table(
    fens: Iterable[str],
    csv_path: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Convert FEN strings into piece/square records.

    Parameters
    ----------
    fens:
        Iterable of Forsyth-Edwards Notation strings.
    csv_path:
        Optional output path.  When provided the extracted table is written as
        a CSV file suitable for :mod:`analysis.heatmaps.generate_heatmaps.R`.

    Returns
    -------
    List[Dict[str, str]]
        A list of ``{"fen_id", "piece", "to"}`` dictionaries for every piece
        occurrence in *fens*.
    """

    records: List[Dict[str, str]] = []

    for idx, fen in enumerate(fens):
        board = chess.Board(fen)
        for square, piece in board.piece_map().items():
            records.append(
                {
                    "fen_id": str(idx),
                    "piece": chess.piece_name(piece.piece_type),
                    "to": chess.square_name(square),
                }
            )

    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["fen_id", "piece", "to"])
            writer.writeheader()
            writer.writerows(records)

    return records


def export_agent_metrics(
    metrics: Dict[str, Any],
    csv_path: Optional[str] = None,
    json_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Write agent metrics to CSV and/or JSON files.

    Parameters
    ----------
    metrics:
        Mapping of metric names to their values.
    csv_path, json_path:
        Optional paths for CSV or JSON output. When provided the mapping is
        written to the respective format.

    Returns
    -------
    Dict[str, Any]
        The *metrics* mapping for convenience.
    """

    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["metric", "value"])
            for key, value in metrics.items():
                writer.writerow([key, value])

    if json_path:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh)

    return metrics


def export_scenarios(
    fens: Iterable[str],
    csv_path: Optional[str] = None,
    json_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Detect scenarios for a sequence of FEN strings.

    Each FEN is analysed using :func:`scenarios.detect_scenarios`.  The
    returned scenarios are augmented with a ``fen_id`` field referencing the
    original position.  Results can be written to CSV or JSON files.

    Parameters
    ----------
    fens:
        Iterable of FEN strings to analyse.
    csv_path, json_path:
        Optional paths for CSV or JSON output.

    Returns
    -------
    List[Dict[str, Any]]
        Detected scenarios with the originating ``fen_id``.
    """

    records: List[Dict[str, Any]] = []
    for idx, fen in enumerate(fens):
        for sc in detect_scenarios(fen):
            rec: Dict[str, Any] = {"fen_id": str(idx)}
            rec.update(sc)
            records.append(rec)

    if csv_path and records:
        fieldnames = sorted({k for r in records for k in r.keys()})
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                row = {
                    k: json.dumps(v) if isinstance(v, (list, dict)) else v
                    for k, v in r.items()
                }
                writer.writerow(row)
    elif csv_path:
        # Write an empty file with standard headers if no scenarios were found
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["fen_id", "id", "square", "color", "side", "targets"])

    if json_path:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(records, fh)

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
        help="Limit the number of games processed",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed for deterministic sampling",
    )
    args = parser.parse_args()
    records, stats = export_move_table(
        args.path,
        csv_path=args.csv_path,
        rds_path=args.rds_path,
        sample_size=args.sample_size,
        seed=args.seed,
    )
    print(
        f"Processed {stats['games']} games with {stats['moves']} moves",
        flush=True,
    )
