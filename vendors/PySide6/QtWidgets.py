"""Minimal QtWidgets stubs for headless testing."""

from __future__ import annotations

from typing import Any, List, Optional

from .QtCore import Qt, Signal


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

    def setVisible(self, visible: bool) -> None:
        self._visible = visible

    def isVisible(self) -> bool:  # pragma: no cover - trivial
        return self._visible

    def setLayout(self, layout: Any) -> None:  # pragma: no cover - trivial
        self._layout = layout

    def close(self) -> None:  # pragma: no cover - trivial
        pass


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
