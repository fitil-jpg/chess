"""Minimal stubs for PySide6.QtGui used in tests."""

from __future__ import annotations

from typing import Any, Dict, List

from .QtCore import Qt


class QStandardItem:
    def __init__(self, text: str = "") -> None:
        self._text = text
        self._data: Dict[int, Any] = {}
        self._children: List[QStandardItem] = []

    # --------------------------------------------------------------
    def appendRow(self, item: "QStandardItem") -> None:
        self._children.append(item)

    # --------------------------------------------------------------
    def text(self) -> str:  # pragma: no cover - trivial
        return self._text

    # --------------------------------------------------------------
    def setData(self, value: Any, role: int) -> None:
        self._data[role] = value

    # --------------------------------------------------------------
    def data(self, role: int) -> Any:
        return self._data.get(role)

    # --------------------------------------------------------------
    def child(self, row: int) -> "QStandardItem":
        return self._children[row]

    # --------------------------------------------------------------
    def rowCount(self) -> int:
        return len(self._children)


class QStandardItemModel:
    def __init__(self) -> None:
        self._roots: List[QStandardItem] = []
        self._headers: List[str] = []

    # --------------------------------------------------------------
    def clear(self) -> None:
        self._roots.clear()

    # --------------------------------------------------------------
    def setHorizontalHeaderLabels(self, labels: List[str]) -> None:  # pragma: no cover - trivial
        self._headers = list(labels)

    # --------------------------------------------------------------
    def appendRow(self, item: QStandardItem) -> None:
        self._roots.append(item)

    # --------------------------------------------------------------
    def rowCount(self) -> int:
        return len(self._roots)

    # --------------------------------------------------------------
    def item(self, row: int) -> QStandardItem:
        return self._roots[row]
