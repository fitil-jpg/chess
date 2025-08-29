import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from ui.panels import create_heatmap_panel


def test_heatmap_panel_selection_triggers_callback():
    app = QApplication.instance() or QApplication([])
    selected = []
    layout, combo = create_heatmap_panel(lambda p: selected.append(p))
    combo.setCurrentText("knight")
    assert selected[-1] == "knight"
    combo.setCurrentText("none")
    assert selected[-1] is None
