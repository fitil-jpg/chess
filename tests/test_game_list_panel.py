from vendors import setup_path  # noqa: F401

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.game_list_panel import GameListPanel, GameListModel


def _visible_ids(panel):
    model = panel.proxy
    ids = []
    for row in range(model.rowCount()):
        idx = model.index(row, 0)
        run = model.data(idx, GameListModel.RUN_ROLE)
        ids.append(run.get("game_id"))
    return ids


def test_sort_by_result_and_date():
    app = QApplication.instance() or QApplication([])
    runs = [
        {"game_id": "g1", "result": "0-1", "date": "2024-01-03"},
        {"game_id": "g2", "result": "1-0", "date": "2024-01-02"},
        {"game_id": "g3", "result": "1/2-1/2", "date": "2024-01-01"},
    ]
    panel = GameListPanel(runs)

    assert _visible_ids(panel) == ["g2", "g1", "g3"]

    panel.sort_combo.setCurrentIndex(1)  # Run Date
    assert _visible_ids(panel) == ["g1", "g2", "g3"]
    panel.close()


def test_group_by_date():
    app = QApplication.instance() or QApplication([])
    runs = [
        {"game_id": "g1", "result": "0-1", "date": "2024-01-03"},
        {"game_id": "g2", "result": "1-0", "date": "2024-01-02"},
        {"game_id": "g3", "result": "1/2-1/2", "date": "2024-01-03"},
    ]
    panel = GameListPanel(runs)
    panel.group_checkbox.setChecked(True)
    model = panel.tree_model
    roots = [model.item(i).text() for i in range(model.rowCount())]
    assert roots == ["2024-01-03", "2024-01-02"]
    first_children = {
        model.item(0).child(i).data(Qt.UserRole)["game_id"]
        for i in range(model.item(0).rowCount())
    }
    assert first_children == {"g1", "g3"}
    panel.close()


if __name__ == "__main__":
    test_sort_by_result_and_date()
