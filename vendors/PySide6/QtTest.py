"""Minimal stubs for the QtTest module used in unit tests."""

from __future__ import annotations

from typing import List

from .QtCore import QPoint, Qt
from .QtGui import QMouseEvent


class QSignalSpy(list):
    """Record emissions from a :class:`Signal`."""

    def __init__(self, signal) -> None:  # pragma: no cover - trivial
        super().__init__()
        self._signal = signal
        signal.connect(self._record)

    def _record(self, *args) -> None:  # pragma: no cover - trivial
        self.append(list(args))

    def count(self) -> int:  # pragma: no cover - trivial
        return len(self)


class QTest:
    """Very small subset of QtTest helpers."""

    @staticmethod
    def mouseClick(widget, button: int, modifier: int = Qt.NoModifier, pos: QPoint | None = None) -> None:  # pragma: no cover - trivial
        pos = pos or QPoint(0, 0)
        ev = QMouseEvent(button, pos)
        widget.mousePressEvent(ev)


__all__ = ["QTest", "QSignalSpy"]

