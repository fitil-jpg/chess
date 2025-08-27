from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repository root and vendored packages are importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
VENDOR_PATH = ROOT / "vendors"
if VENDOR_PATH.exists() and str(VENDOR_PATH) not in sys.path:
    sys.path.insert(0, str(VENDOR_PATH))

from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage


def main(argv: list[str] | None = None) -> int:
    """Print bot usage counts aggregated across run files.

    Example
    -------
    Run the script from the repository root:

        python scripts/bot_usage_stats.py --runs runs/
    """
    parser = argparse.ArgumentParser(
        description="Display aggregate bot usage statistics from run files."
    )
    parser.add_argument(
        "--runs",
        default="runs/",
        help="Directory containing run JSON files",
    )
    args = parser.parse_args(argv)

    runs = load_runs(args.runs)
    counts = aggregate_module_usage(runs)

    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - manual usage
    raise SystemExit(main())
