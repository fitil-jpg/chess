import json
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from pyside_viewer import ChessViewer
from ui.drawer_manager import DrawerManager


def test_chess_viewer_applies_heatmap_overlay(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])

    heatmap_dir = tmp_path / "analysis" / "heatmaps"
    heatmap_dir.mkdir(parents=True)
    heatmap_grid = [[0.2 for _ in range(8)] for _ in range(8)]
    (heatmap_dir / "pawn.json").write_text(json.dumps(heatmap_grid), encoding="utf-8")

    def fake_load_heatmaps(self):
        loaded = {}
        for path in heatmap_dir.glob("*.json"):
            with path.open("r", encoding="utf-8") as fh:
                loaded[path.stem] = json.load(fh)
        return loaded

    monkeypatch.setattr(DrawerManager, "_load_heatmaps", fake_load_heatmaps)

    viewer = ChessViewer()

    overlays = viewer.drawer_manager.get_cell_overlays(0, 0)
    assert any(kind == "gradient" for kind, _ in overlays)

    viewer.close()
