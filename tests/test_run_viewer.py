import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

import run_viewer


def test_run_viewer_aggregates_module_usage(monkeypatch):
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
    monkeypatch.setattr(run_viewer, "load_runs", lambda path: runs)
    viewer = run_viewer.RunViewer()
    expected = {"A": 3, "B": 2}
    assert viewer.usage_pie.counts == expected
    viewer.close()
