from vendors import setup_path  # noqa: F401

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from ui.run_selector_window import RunSelectorWindow


def test_run_selector_aggregates_module_usage():
    app = QApplication.instance() or QApplication([])
    runs = [
        {
            "game_id": "g1",
            "result": "1-0",
            "moves": [],
            "fens": [],
            "modules_w": ["A"],
            "modules_b": ["B"],
        },
        {
            "game_id": "g2",
            "result": "0-1",
            "moves": [],
            "fens": [],
            "modules_w": ["A"],
            "modules_b": ["A", "B"],
        },
    ]
    window = RunSelectorWindow(runs)
    expected = {"A": 3, "B": 2}
    assert window.usage_counts == expected
    assert window.usage_pie.counts == expected
    window.close()


if __name__ == "__main__":
    test_run_selector_aggregates_module_usage()

