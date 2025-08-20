from __future__ import annotations

"""Simple pie chart visualising aggregated module usage."""

from typing import Mapping, Dict

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget

from utils.module_colors import MODULE_COLORS


class UsagePie(QWidget):
    """Draw a pie chart representing module usage share."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.counts: Dict[str, int] = {}
        self.setMinimumHeight(100)

    def set_counts(self, counts: Mapping[str, int]) -> None:
        """Set *counts* mapping module name to occurrence count."""

        self.counts = {k: int(v) for k, v in counts.items() if v}
        self.update()

    # ------------------------------------------------------------------
    def paintEvent(self, ev) -> None:  # pragma: no cover - GUI drawing
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))

        total = sum(self.counts.values())
        if total <= 0:
            return

        size = min(self.width(), self.height()) - 20
        rect = QRect((self.width() - size) // 2, (self.height() - size) // 2, size, size)

        start = 0.0
        for key in sorted(self.counts, key=self.counts.get, reverse=True):
            span = self.counts[key] / total * 360
            color = MODULE_COLORS.get(key, MODULE_COLORS["OTHER"])
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawPie(rect, int(start * 16), int(span * 16))
            start += span
