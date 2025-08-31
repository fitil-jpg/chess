from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root and vendored packages are importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
VENDOR_PATH = ROOT / "vendors"
if VENDOR_PATH.exists() and str(VENDOR_PATH) not in sys.path:
    sys.path.insert(0, str(VENDOR_PATH))

import importlib.util

USAGE_LOGGER_PATH = ROOT / "utils" / "usage_logger.py"
spec = importlib.util.spec_from_file_location("usage_logger", USAGE_LOGGER_PATH)
usage_logger = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(usage_logger)  # type: ignore[assignment]
read_usage = usage_logger.read_usage


def main(argv: list[str] | None = None) -> int:
    """Display usage counters in a simple text table.

    The counters are read from ``stats/usage_counts.json`` which tracks how
    often various scripts or modules have been run.  The output shows each
    entry's count along with an ASCII bar for quick comparison.
    """
    counts = read_usage()
    if not counts:
        print("No usage data found.")
        return 0

    width = max(len(path) for path in counts)
    max_count = max(counts.values())
    scale = 40 / max_count if max_count else 1

    header = f"{'Path':<{width}} | Count | Chart"
    print(header)
    print("-" * len(header))
    for path, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        bar = "#" * int(count * scale)
        print(f"{path:<{width}} | {count:>5} | {bar}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual usage
    raise SystemExit(main())
