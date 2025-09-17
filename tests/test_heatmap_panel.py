import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from ui.panels import create_heatmap_panel


def test_heatmap_panel_selection_triggers_callback():
    app = QApplication.instance() or QApplication([])
    selected = []
    layout, set_combo, piece_combo = create_heatmap_panel(
        lambda p: selected.append(p),
        sets=["default"],
        pieces=["knight", "rook"],
        current_set="default",
        current_piece="knight",
    )
    assert set_combo.count() == 1
    piece_combo.setCurrentText("rook")
    assert selected[-1] == "rook"
    piece_combo.setCurrentText("none")
    assert selected[-1] is None


def test_heatmap_panel_set_callback():
    app = QApplication.instance() or QApplication([])
    selected_sets = []
    layout, set_combo, piece_combo = create_heatmap_panel(
        lambda _: None,
        set_callback=lambda name: selected_sets.append(name),
        sets=["default", "alt"],
    )
    assert piece_combo.count() >= 1  # includes "none"
    set_combo.setCurrentText("alt")
    assert selected_sets[-1] == "alt"
