"""Entry point for selecting recorded runs.

Usage:
    python run_selector.py --runs path/to/dir
"""

from utils.usage_logger import record_usage
record_usage(__file__)

import argparse
import sys

from PySide6.QtWidgets import QApplication

from utils.load_runs import load_runs
from ui.run_selector_window import RunSelectorWindow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run selector GUI")
    parser.add_argument(
        "--runs", default="runs/", help="Directory containing run JSON files"
    )
    args = parser.parse_args(argv)

    runs = load_runs(args.runs)

    app = QApplication(sys.argv)
    window = RunSelectorWindow(runs)
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover - manual usage
    sys.exit(main())
