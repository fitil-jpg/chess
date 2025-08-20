"""Minimal QtWidgets stubs for headless testing."""

from __future__ import annotations

from typing import Any, List, Optional

from .QtCore import Qt, Signal, QRect


class QApplication:
    _instance: Optional["QApplication"] = None

    def __init__(self, args: List[str]) -> None:  # pragma: no cover - trivial
        QApplication._instance = self

    @staticmethod
    def instance() -> Optional["QApplication"]:  # pragma: no cover - trivial
        return QApplication._instance

    def exec(self) -> int:  # pragma: no cover - trivial
        return 0


class QWidget:
    def __init__(self, parent: Optional["QWidget"] = None) -> None:  # pragma: no cover - trivial
        self._visible = True
        self._layout: Optional[Any] = None
        self._w = 100
        self._h = 30
        self._min_w = 0
        self._min_h = 0

    def setVisible(self, visible: bool) -> None:
        self._visible = visible

    def isVisible(self) -> bool:  # pragma: no cover - trivial
        return self._visible

    def setLayout(self, layout: Any) -> None:  # pragma: no cover - trivial
        self._layout = layout

    def close(self) -> None:  # pragma: no cover - trivial
        pass

    def resize(self, w: int, h: int) -> None:  # pragma: no cover - trivial
        self._w, self._h = w, h

    def width(self) -> int:  # pragma: no cover - trivial
        return self._w

    def height(self) -> int:  # pragma: no cover - trivial
        return self._h

    def rect(self) -> QRect:  # pragma: no cover - trivial
        return QRect(0, 0, self._w, self._h)

    def setMinimumSize(self, w: int, h: int) -> None:  # pragma: no cover - trivial
        self._min_w, self._min_h = w, h

    def setMinimumHeight(self, h: int) -> None:  # pragma: no cover - trivial
        self._min_h = h

    def show(self) -> None:  # pragma: no cover - trivial
        self.setVisible(True)

    def setAttribute(self, attr: int) -> None:  # pragma: no cover - trivial
        pass

    def update(self) -> None:  # pragma: no cover - trivial
        pass

    def setWindowTitle(self, title: str) -> None:  # pragma: no cover - trivial
        self._title = title


class QListView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.model: Any = None

    def setModel(self, model: Any) -> None:
        self.model = model


class QTreeView(QListView):
    def setModel(self, model: Any) -> None:
        self.model = model

    def setHeaderHidden(self, hidden: bool) -> None:  # pragma: no cover - trivial
        self._header_hidden = hidden

    def hide(self) -> None:
        self.setVisible(False)


class QFrame(QWidget):
    def setFixedSize(self, w: int, h: int) -> None:  # pragma: no cover - trivial
        self.resize(w, h)


class QGridLayout:
    def __init__(self, parent: Optional[QWidget] = None) -> None:  # pragma: no cover - trivial
        self._items: List[tuple[Any, int, int]] = []
        if parent is not None:
            parent.setLayout(self)

    def setContentsMargins(self, *args) -> None:  # pragma: no cover - trivial
        pass

    def addWidget(self, widget: Any, row: int, col: int) -> None:  # pragma: no cover - trivial
        self._items.append((widget, row, col))

    def setSpacing(self, spacing: int) -> None:  # pragma: no cover - trivial
        pass


class QVBoxLayout:
    def __init__(self, parent: Optional[QWidget] = None) -> None:  # pragma: no cover - trivial
        self._items: List[Any] = []
        if parent is not None:
            parent.setLayout(self)

    def addWidget(self, widget: Any) -> None:
        self._items.append(widget)

    def addLayout(self, layout: "QVBoxLayout") -> None:
        self._items.append(layout)


class QHBoxLayout(QVBoxLayout):
    pass


class QComboBox(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._items: List[tuple[str, Any]] = []
        self._current_index = 0
        self.currentIndexChanged = Signal()

    def addItem(self, text: str, userData: Any = None) -> None:
        self._items.append((text, userData))

    def itemData(self, index: int) -> Any:
        return self._items[index][1]

    def setCurrentIndex(self, index: int) -> None:
        self._current_index = index
        self.currentIndexChanged.emit(index)

    def currentIndex(self) -> int:  # pragma: no cover - trivial
        return self._current_index


class QCheckBox(QWidget):
    def __init__(self, text: str = "") -> None:
        super().__init__()
        self.text = text
        self._checked = False
        self.toggled = Signal()

    def setChecked(self, checked: bool) -> None:
        self._checked = checked
        self.toggled.emit(checked)

    def isChecked(self) -> bool:  # pragma: no cover - trivial
        return self._checked


class QLabel(QWidget):
    def __init__(self, text: str = "") -> None:  # pragma: no cover - trivial
        super().__init__()
        self._text = text
        self._font = None
        self._alignment = Qt.AlignCenter
        self._palette = None

    def setText(self, text: str) -> None:  # pragma: no cover - trivial
        self._text = text

    def text(self) -> str:  # pragma: no cover - trivial
        return self._text

    def setFixedSize(self, w: int, h: int) -> None:  # pragma: no cover - trivial
        self.resize(w, h)

    def setAlignment(self, align: int) -> None:  # pragma: no cover - trivial
        self._alignment = align

    def setFont(self, font) -> None:  # pragma: no cover - trivial
        self._font = font

    def setAutoFillBackground(self, enabled: bool) -> None:  # pragma: no cover - trivial
        pass

    def palette(self):  # pragma: no cover - trivial
        from PySide6.QtGui import QPalette

        return self._palette or QPalette()

    def setPalette(self, palette) -> None:  # pragma: no cover - trivial
        self._palette = palette


class QListWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._items: List[str] = []
        self.currentRowChanged = Signal()
        self._current = -1

    def addItem(self, text: str) -> None:
        self._items.append(text)

    def setCurrentRow(self, row: int) -> None:
        self._current = row
        self.currentRowChanged.emit(row)

    def currentRow(self) -> int:  # pragma: no cover - trivial
        return self._current

    def clear(self) -> None:
        self._items.clear()

    def count(self) -> int:  # pragma: no cover - trivial
        return len(self._items)
