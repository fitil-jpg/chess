"""Convenience wrappers for FEN parsing, heatmap generation and metrics.

This module exposes a tiny API that other projects can use to interact
with the chess analysis tools provided by this repository.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable, List, Dict, Any

import chess

from fen_handler import fen_to_board_state
from analysis.loader import export_fen_table
from metrics import MetricsManager


def parse_fen(fen: str) -> List[List[str | None]]:
    """Return a board representation for *fen*.

    The board is represented as an 8×8 list where each entry is a piece
    name or ``None`` for empty squares.
    """

    return fen_to_board_state(fen)


def generate_heatmaps(
    fens: Iterable[str],
    out_dir: str = "analysis/heatmaps",
) -> Dict[str, List[List[int]]]:
    """Generate heatmaps for *fens* and return them as dictionaries.

    This function serialises ``fens`` into a CSV file and invokes the
    :mod:`analysis.heatmaps.generate_heatmaps.R` script via ``Rscript``.
    The resulting JSON heatmaps are loaded and returned as a mapping from
    ``fen_id`` to 8×8 integer matrices.
    """

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    csv_path = out_path / "fens.csv"
    export_fen_table(fens, csv_path=str(csv_path))

    script = Path("analysis/heatmaps/generate_heatmaps.R")
    try:
        subprocess.run(["Rscript", str(script), str(csv_path)], check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Rscript not found; install R to generate heatmaps"
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Rscript failed: {exc}") from exc

    heatmaps: Dict[str, List[List[int]]] = {}
    for json_file in out_path.glob("heatmap_*.json"):
        with json_file.open("r", encoding="utf-8") as fh:
            heatmaps[json_file.stem.replace("heatmap_", "")] = json.load(fh)
    return heatmaps


def compute_metrics(fen: str) -> Dict[str, Dict[str, Any]]:
    """Compute short- and long-term metrics for *fen*.

    The returned dictionary contains two keys, ``short_term`` and
    ``long_term``, each mapping metric names to integer scores.
    """

    board = chess.Board(fen)
    mgr = MetricsManager(board)
    mgr.update_all_metrics()
    return mgr.get_metrics()


__all__ = ["parse_fen", "generate_heatmaps", "compute_metrics"]
