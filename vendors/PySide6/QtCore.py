"""Minimal stub implementations of PySide6.QtCore classes used in tests.
This is not a full-featured Qt binding but provides just enough
functionality for the project's unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cmp_to_key
from typing import Any, Callable, List, Optional


class Qt:
    """Subset of the Qt enum values used by the project."""

    DisplayRole = 0
    UserRole = 256
    AscendingOrder = 0
    DescendingOrder = 1


class Signal:
    """Very small replacement for Qt's signal/slot mechanism."""

    def __init__(self) -> None:
        self._slots: List[Callable[..., None]] = []

    def connect(self, slot: Callable[..., None]) -> None:
        self._slots.append(slot)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for slot in list(self._slots):
            slot(*args, **kwargs)


@dataclass
class QModelIndex:
    """Simple stand-in for QModelIndex handling only row access."""

    _row: Optional[int] = None

    def row(self) -> int:
        return -1 if self._row is None else self._row

    def isValid(self) -> bool:  # pragma: no cover - trivial
        return self._row is not None


class QAbstractListModel:
    """Base class implementing minimal Qt model behaviour."""

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # pragma: no cover - interface only
        return 0

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # pragma: no cover - interface only
        return None

    # Qt models use begin/endResetModel around data resets; here they are
    # simple no-ops so the API is compatible with the real library.
    def beginResetModel(self) -> None:  # pragma: no cover - trivial
        pass

    def endResetModel(self) -> None:  # pragma: no cover - trivial
        pass


class QSortFilterProxyModel(QAbstractListModel):
    """Very small proxy model supporting custom ``lessThan`` sorting."""

    def __init__(self) -> None:
        super().__init__()
        self._source_model: Optional[QAbstractListModel] = None
        self._rows: List[int] = []

    # --------------------------------------------------------------
    def setSourceModel(self, model: QAbstractListModel) -> None:
        self._source_model = model
        self.invalidate()

    # --------------------------------------------------------------
    def sourceModel(self) -> Optional[QAbstractListModel]:  # pragma: no cover - trivial
        return self._source_model

    # --------------------------------------------------------------
    def invalidate(self) -> None:
        if self._source_model is not None:
            self._rows = list(range(self._source_model.rowCount()))
        else:
            self._rows = []

    # --------------------------------------------------------------
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    # --------------------------------------------------------------
    def index(self, row: int, column: int) -> QModelIndex:
        if 0 <= row < len(self._rows):
            return QModelIndex(self._rows[row])
        return QModelIndex()

    # --------------------------------------------------------------
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if self._source_model is None or not index.isValid():
            return None
        return self._source_model.data(QModelIndex(index.row()), role)

    # --------------------------------------------------------------
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # pragma: no cover - overridden in subclass
        return left.row() < right.row()

    # --------------------------------------------------------------
    def sort(self, column: int, order: int = Qt.AscendingOrder) -> None:
        if self._source_model is None:
            self._rows = []
            return

        def cmp(l: int, r: int) -> int:
            li = QModelIndex(l)
            ri = QModelIndex(r)
            if self.lessThan(li, ri):
                return -1
            if self.lessThan(ri, li):
                return 1
            return 0

        self._rows = list(range(self._source_model.rowCount()))
        self._rows.sort(key=cmp_to_key(cmp))
        if order == Qt.DescendingOrder:
            self._rows.reverse()
