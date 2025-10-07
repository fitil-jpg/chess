"""Compute and (optionally) plot a reliability diagram from CSV inputs.

Usage:
  python -m scripts.reliability_diagram preds.csv labels.csv --bins 15 --plot out.png

Both CSV files should contain a single column of floats (0..1) and integers
{0,1} respectively. If --plot is omitted, the script prints ECE and a tabular
summary to stdout.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from metrics.calibration import expected_calibration_error, reliability_curve, plot_reliability_diagram


def _read_single_column_csv(path: Path) -> List[float]:
    vals: List[float] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                vals.append(float(line.split(",")[0]))
            except Exception:
                # skip header or malformed lines
                continue
    return vals


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("preds", type=Path, help="CSV file with predicted probabilities [0,1]")
    ap.add_argument("labels", type=Path, help="CSV file with labels {0,1}")
    ap.add_argument("--bins", type=int, default=10, help="Number of bins (default: 10)")
    ap.add_argument("--plot", type=Path, default=None, help="Output PNG path to save a diagram")
    args = ap.parse_args()

    p = _read_single_column_csv(args.preds)
    y = [int(v) for v in _read_single_column_csv(args.labels)]

    ece = expected_calibration_error(p, y, num_bins=args.bins)
    centers, accs, confs, counts = reliability_curve(p, y, num_bins=args.bins)
    print(f"ECE={ece:.4f}")
    print("bin_center,acc,conf,count")
    for c, a, cf, n in zip(centers, accs, confs, counts):
        print(f"{c:.3f},{a:.3f},{cf:.3f},{n}")

    if args.plot is not None:
        fig = plot_reliability_diagram(p, y, num_bins=args.bins)
        if fig is None:
            print("matplotlib not available; skipping plot")
        else:
            fig.savefig(args.plot, dpi=150, bbox_inches="tight")
            print(f"Saved diagram to {args.plot}")


if __name__ == "__main__":
    main()

