#!/usr/bin/env python3
"""Generate heatmaps from recorded runs.

Reads JSON files in a runs directory, converts their FENs into per-piece
tables and calls the heatmap generator integration. Outputs JSON/CSV heatmaps
under analysis/heatmaps (or a provided directory) for use in the UI.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from analysis.loader import export_fen_table
from utils.integration import generate_heatmaps
from utils.load_runs import load_runs


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build heatmaps from run FENs")
    p.add_argument("--runs", default="runs", help="Directory with run JSON files")
    p.add_argument("--out", default="analysis/heatmaps", help="Output base directory")
    p.add_argument("--pattern-set", default="default", help="Heatmap set name")
    p.add_argument("--wolfram", action="store_true", help="Use Wolfram instead of R")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    runs = load_runs(args.runs)
    fens: list[str] = []
    for run in runs:
        fens.extend(run.get("fens", []))
    if not fens:
        print("No FENs found in runs; nothing to do")
        return 0

    # Materialize CSV first (also useful for external tools)
    out_dir = Path(args.out) / args.pattern_set
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "fens.csv"
    export_fen_table(fens, csv_path=str(csv_path))

    # Now invoke R/Wolfram pipeline via integration
    result = generate_heatmaps(
        fens,
        out_dir=args.out,
        pattern_set=args.pattern_set,
        use_wolfram=args.wolfram,
    )
    print(f"Generated heatmaps for set '{args.pattern_set}' in {out_dir}")
    print(f"Pieces: {', '.join(sorted(result.get(args.pattern_set, {}).keys()))}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI utility
    raise SystemExit(main())
