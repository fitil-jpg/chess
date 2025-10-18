"""Convenience wrappers for FEN parsing, heatmap generation and metrics.

This module exposes a tiny API that other projects can use to interact
with the chess analysis tools provided by this repository.
"""

from __future__ import annotations

import json
import subprocess
import logging
logger = logging.getLogger(__name__)

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

    try:
        return fen_to_board_state(fen)
    except Exception as exc:
        raise ValueError(f"❌ Failed to parse FEN string: {exc}\n\n<b>FEN:</b> {fen}") from exc


def generate_heatmaps(
    fens: Iterable[str],
    out_dir: str | Path | None = None,
    pattern_set: str = "default",
    use_wolfram: bool = False,
) -> Dict[str, Dict[str, List[List[int]]]]:
    """Generate heatmaps for *fens* and return them as dictionaries.

    This function serialises ``fens`` into a CSV file and invokes either the
    R or Wolfram heatmap scripts.  When ``use_wolfram`` is ``False`` (the
    default) ``analysis/heatmaps/generate_heatmaps.R`` is executed via
    ``Rscript``.  When ``True`` the Wolfram Language implementation
    ``analysis/heatmaps/generate_heatmaps.wl`` is run via ``wolframscript``.
    The resulting JSON heatmaps are loaded from ``analysis/heatmaps/<pattern_set>``
    (or ``out_dir/<pattern_set>`` when ``out_dir`` is provided) and returned as
    ``{pattern_set: {fen_id: matrix}}`` with each matrix being an 8×8 grid of
    integers.
    """

    base_path = Path(out_dir) if out_dir is not None else Path("analysis/heatmaps")
    out_path = base_path / pattern_set
    out_path.mkdir(parents=True, exist_ok=True)
    csv_path = out_path / "fens.csv"
    export_fen_table(fens, csv_path=str(csv_path))

    if use_wolfram:
        script = Path("analysis/heatmaps/generate_heatmaps.wl")
        cmd = ["wolframscript", "-file", str(script), str(csv_path)]
        missing = "wolframscript not found; install Wolfram Engine to generate heatmaps"
        fail_msg = "wolframscript failed"
    else:
        # Try R first, fallback to Python
        script = Path("analysis/heatmaps/generate_heatmaps.R")
        cmd = ["Rscript", str(script), str(csv_path)]
        missing = "Rscript not found; install R to generate heatmaps"
        fail_msg = "Rscript failed"
        
        # Check if R is available
        try:
            import subprocess
            subprocess.run(["Rscript", "--version"], check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback to Python implementation
            script = Path("analysis/heatmaps/generate_heatmaps_python.py")
            cmd = ["python3", str(script), str(csv_path), str(out_path)]
            missing = "Python not found; install Python to generate heatmaps"
            fail_msg = "Python heatmap generation failed"

    try:
        logger.info(f"🔄 Executing heatmap generation: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("✅ Heatmap generation completed successfully")
    except FileNotFoundError as exc:
        error_msg = f"{missing}\n\n<b>Installation instructions:</b>\n"
        if use_wolfram:
            error_msg += "• Download Wolfram Engine from https://www.wolfram.com/engine/\n"
            error_msg += "• Install and ensure 'wolframscript' is in your PATH\n"
        else:
            error_msg += "• Install R from https://www.r-project.org/\n"
            error_msg += "• Install required R packages: install.packages(c('jsonlite', 'ggplot2'))\n"
        error_msg += f"\n<b>Command attempted:</b> {' '.join(cmd)}"
        raise RuntimeError(error_msg) from exc
    except subprocess.CalledProcessError as exc:
        error_msg = f"{fail_msg}\n\n<b>Error details:</b>\n"
        error_msg += f"• Exit code: {exc.returncode}\n"
        if exc.stdout:
            error_msg += f"• Output: {exc.stdout}\n"
        if exc.stderr:
            error_msg += f"• Error: {exc.stderr}\n"
        error_msg += f"\n<b>Command:</b> {' '.join(cmd)}"
        raise RuntimeError(error_msg) from exc

    heatmaps: Dict[str, List[List[int]]] = {}
    heatmap_files = list(out_path.glob("heatmap_*.json"))
    if not heatmap_files:
        error_msg = f"❌ No heatmap files generated in {out_path}\n\n"
        error_msg += f"<b>Expected files:</b> heatmap_*.json\n"
        error_msg += f"<b>Directory contents:</b>\n"
        try:
            files = list(out_path.iterdir())
            if files:
                error_msg += "\n".join(f"• {f.name}" for f in files)
            else:
                error_msg += "• (empty directory)"
        except Exception:
            error_msg += "• (cannot list directory)"
        error_msg += f"\n\n<b>Possible causes:</b>\n"
        error_msg += f"• Script failed to generate output files\n"
        error_msg += f"• Wrong output directory specified\n"
        error_msg += f"• Permission issues\n"
        error_msg += f"• Script syntax errors"
        raise RuntimeError(error_msg)
    
    for json_file in heatmap_files:
        try:
            with json_file.open("r", encoding="utf-8") as fh:
                heatmaps[json_file.stem.replace("heatmap_", "")] = json.load(fh)
        except Exception as exc:
            logger.warning(f"Failed to load heatmap file {json_file}: {exc}")
            continue
    
    if not heatmaps:
        raise RuntimeError(f"❌ No valid heatmap files could be loaded from {out_path}")
    
    logger.info(f"✅ Loaded {len(heatmaps)} heatmap files")
    return {pattern_set: heatmaps}


def compute_metrics(fen: str) -> Dict[str, Dict[str, Any]]:
    """Compute short- and long-term metrics for *fen*.

    The returned dictionary contains two keys, ``short_term`` and
    ``long_term``, each mapping metric names to integer scores.
    """

    try:
        board = chess.Board(fen)
    except ValueError as exc:
        raise ValueError(f"❌ Invalid FEN string: {exc}\n\n<b>FEN:</b> {fen}") from exc
    except Exception as exc:
        raise RuntimeError(f"❌ Failed to create board from FEN: {exc}\n\n<b>FEN:</b> {fen}") from exc

    try:
        mgr = MetricsManager(board)
        mgr.update_all_metrics()
        return mgr.get_metrics()
    except Exception as exc:
        raise RuntimeError(f"❌ Failed to compute metrics: {exc}\n\n<b>FEN:</b> {fen}") from exc


__all__ = ["parse_fen", "generate_heatmaps", "compute_metrics"]
