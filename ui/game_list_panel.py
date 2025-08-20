"""Game list panel with sorting options.

This module provides ``GameListPanel`` which displays a list of recorded
chess games and allows the user to sort them either by the result or by
run date.  Sorting is implemented using :class:`QSortFilterProxyModel`
and a small custom ``GameListModel``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Dict, Any

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    QSortFilterProxyModel,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QListView,
    QTreeView,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QCheckBox,
)


class GameListModel(QAbstractListModel):
    """Simple list model storing run dictionaries."""

    RESULT_ROLE = Qt.UserRole + 1
    DATE_ROLE = Qt.UserRole + 2
    RUN_ROLE = Qt.UserRole + 3

    def __init__(self, runs: Iterable[Dict[str, Any]] | None = None):
        super().__init__()
        self._runs: List[Dict[str, Any]] = list(runs or [])

    # ------------------------------------------------------------------
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # pragma: no cover - trivial
        return len(self._runs)

    # ------------------------------------------------------------------
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._runs)):
            return None
        run = self._runs[index.row()]
        if role == Qt.DisplayRole:
            game_id = run.get("game_id", "<unknown>")
            result: str | None = run.get("result")
            return (
                f"{game_id} ({result})"
                if result and result != "*"
                else game_id
            )
        if role == self.RESULT_ROLE:
            return run.get("result")
        if role == self.DATE_ROLE:
            return run.get("date")
        if role == self.RUN_ROLE:
            return run
        return None

    # ------------------------------------------------------------------
    def set_runs(self, runs: Iterable[Dict[str, Any]]) -> None:
        """Replace the model data with *runs* and reset the model."""
        self.beginResetModel()
        self._runs = list(runs)
        self.endResetModel()


class GameListSortProxyModel(QSortFilterProxyModel):
    """Proxy model that provides custom sorting for game lists."""

    def __init__(self):
        super().__init__()
        self.sort_mode: str = "result"

    # ------------------------------------------------------------------
    def set_sort_mode(self, mode: str) -> None:
        self.sort_mode = mode

    # ------------------------------------------------------------------
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # pragma: no cover - logic tested
        src = self.sourceModel()
        if not src:
            return False

        if self.sort_mode == "result":
            l_res = src.data(left, GameListModel.RESULT_ROLE)
            r_res = src.data(right, GameListModel.RESULT_ROLE)
            return self._result_rank(l_res) < self._result_rank(r_res)
        elif self.sort_mode == "date":
            l_date = src.data(left, GameListModel.DATE_ROLE)
            r_date = src.data(right, GameListModel.DATE_ROLE)
            return self._to_datetime(l_date) < self._to_datetime(r_date)
        return super().lessThan(left, right)

    # ------------------------------------------------------------------
    @staticmethod
    def _result_rank(result: str | None) -> int:
        if result == "1-0":
            return 0  # win
        if result == "0-1":
            return 1  # loss
        return 2  # draw or unknown

    # ------------------------------------------------------------------
    @staticmethod
    def _to_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return datetime.min


class GameListPanel(QWidget):
    """Panel displaying a list of games with sorting controls."""

    def __init__(self, runs: Iterable[Dict[str, Any]] | None = None, parent=None):
        super().__init__(parent)
        runs = list(runs or [])

        self.model = GameListModel(runs)
        self.proxy = GameListSortProxyModel()
        self.proxy.setSourceModel(self.model)

        self.list_view = QListView()
        self.list_view.setModel(self.proxy)

        self.tree_model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.hide()

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Result", "result")
        self.sort_combo.addItem("Run Date", "date")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_mode_changed)

        self.group_checkbox = QCheckBox("Group by date")
        self.group_checkbox.toggled.connect(self._on_group_toggled)

        controls = QHBoxLayout()
        controls.addWidget(self.sort_combo)
        controls.addWidget(self.group_checkbox)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.list_view)
        layout.addWidget(self.tree_view)

        # Apply initial sort
        self._on_sort_mode_changed(self.sort_combo.currentIndex())

    # ------------------------------------------------------------------
    def _on_sort_mode_changed(self, index: int) -> None:
        mode = self.sort_combo.itemData(index)
        if mode == "date":
            self.proxy.set_sort_mode("date")
            self.proxy.sort(0, Qt.DescendingOrder)
        else:
            self.proxy.set_sort_mode("result")
            self.proxy.sort(0, Qt.AscendingOrder)

        if self.group_checkbox.isChecked():
            self._populate_tree()

    # ------------------------------------------------------------------
    def _on_group_toggled(self, checked: bool) -> None:
        self.list_view.setVisible(not checked)
        self.tree_view.setVisible(checked)
        if checked:
            self._populate_tree()

    # ------------------------------------------------------------------
    def set_runs(self, runs: Iterable[Dict[str, Any]]) -> None:
        self.model.set_runs(runs)
        self._on_sort_mode_changed(self.sort_combo.currentIndex())
        if self.group_checkbox.isChecked():
            self._populate_tree()

    # ------------------------------------------------------------------
    def _populate_tree(self) -> None:
        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(["Games"])

        groups: Dict[str, List[Dict[str, Any]]] = {}
        for run in self.model._runs:
            date = run.get("date") or ""
            if isinstance(date, datetime):
                key = date.date().isoformat()
            else:
                key = str(date)
            groups.setdefault(key, []).append(run)

        for key in sorted(groups.keys(), reverse=True):
            parent = QStandardItem(key)
            for run in groups[key]:
                game_id = run.get("game_id", "<unknown>")
                result: str | None = run.get("result")
                label = (
                    f"{game_id} ({result})"
                    if result and result != "*"
                    else game_id
                )
                child = QStandardItem(label)
                child.setData(run, Qt.UserRole)
                parent.appendRow(child)
            self.tree_model.appendRow(parent)
