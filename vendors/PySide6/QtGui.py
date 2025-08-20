"""Minimal stubs for PySide6.QtGui used in tests."""

from __future__ import annotations

from typing import Any, Dict, List

from .QtCore import Qt, QPoint


# ---------------------------------------------------------------------------
#  Minimal GUI primitives used in tests
# ---------------------------------------------------------------------------


class QFont:
    """Trivial stand-in for QFont."""

    def __init__(self, family: str = "", size: int | None = None) -> None:  # pragma: no cover - trivial
        self.family = family
        self.size = size or 10

    def setPointSize(self, size: int) -> None:  # pragma: no cover - trivial
        self.size = size


class QFontMetrics:
    """Very small subset of :class:`QFontMetrics`."""

    def __init__(self, font: QFont | None = None) -> None:  # pragma: no cover - trivial
        self._font = font

    def horizontalAdvance(self, text: str) -> int:
        return len(text) * 7

    def ascent(self) -> int:
        return 10


class QPen:
    """Light-weight replacement for QPen."""

    def __init__(self, color: int | None = None) -> None:  # pragma: no cover - trivial
        self.color = color
        self.width = 0

    def setWidth(self, w: int) -> None:  # pragma: no cover - trivial
        self.width = w


class QPainter:
    """Very small subset of :class:`QPainter` used by tests."""

    def __init__(self, widget) -> None:  # pragma: no cover - trivial
        self.widget = widget
        self._font = QFont()
        self._pen = QPen()

    def fillRect(self, *args, **kwargs) -> None:  # pragma: no cover - trivial
        pass

    def setFont(self, font: QFont) -> None:  # pragma: no cover - trivial
        self._font = font

    def fontMetrics(self) -> QFontMetrics:
        return QFontMetrics(self._font)

    def setPen(self, pen: QPen) -> None:  # pragma: no cover - trivial
        self._pen = pen

    def drawLine(self, *args, **kwargs) -> None:  # pragma: no cover - trivial
        pass

    def drawText(self, *args, **kwargs) -> None:  # pragma: no cover - trivial
        pass


class QColor:
    """Minimal RGBA colour representation."""

    def __init__(self, r: int | str, g: int = None, b: int = None):  # type: ignore[assignment]
        if isinstance(r, str):
            r = r.lstrip('#')
            if len(r) == 3:
                r = ''.join(ch * 2 for ch in r)
            val = int(r, 16)
            self.r = (val >> 16) & 0xFF
            self.g = (val >> 8) & 0xFF
            self.b = val & 0xFF
        elif g is None and b is None:
            # Allow constructing from a single int like QColor(0xRRGGBB)
            self.r = (r >> 16) & 0xFF
            self.g = (r >> 8) & 0xFF
            self.b = r & 0xFF
        else:
            self.r = int(r)
            self.g = int(g or 0)
            self.b = int(b or 0)


class QMouseEvent:
    """Very small QMouseEvent for tests."""

    def __init__(self, button: int, pos: QPoint):
        self._button = button
        self._pos = pos

    def button(self) -> int:  # pragma: no cover - trivial
        return self._button

    def position(self) -> QPoint:  # pragma: no cover - trivial
        return self._pos


class QPalette:
    """Very small palette used for background colours."""

    Window = 0

    def __init__(self) -> None:  # pragma: no cover - trivial
        self.colors: Dict[int, QColor] = {}

    def setColor(self, role: int, color: QColor) -> None:  # pragma: no cover - trivial
        self.colors[role] = color

    def pos(self) -> QPoint:  # pragma: no cover - trivial
        return self._pos


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
