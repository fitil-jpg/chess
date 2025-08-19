"""Timeline widget visualising per-move module usage.

Two horizontal lanes represent White (top) and Black (bottom).
Each move is drawn as a coloured rectangle according to the module
that produced it.  Clicking on a rectangle emits the corresponding
move index and colour side.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QPainter, QPen, QFont, QColor, QMouseEvent
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QRect

from utils.module_colors import MODULE_COLORS, REASON_PRIORITY


class UsageTimeline(QWidget):
    """Simple timeline: two rows of tiles (White on top, Black below)."""

    moveClicked = Signal(int, bool)  # index, is_white

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.w_keys: list[str] = []  # list of module keys per White move
        self.b_keys: list[str] = []  # list of module keys per Black move
        self.setMinimumSize(280, 120)

    def set_data(self, w_keys: list[str], b_keys: list[str]) -> None:
        self.w_keys = list(w_keys)
        self.b_keys = list(b_keys)
        self.update()

    def mousePressEvent(self, ev: QMouseEvent) -> None:  # pragma: no cover - UI interaction
        if ev.button() != Qt.LeftButton:
            return
        w = self.width()
        h = self.height()
        pad = 8
        lane_h = (h - pad * 3) // 3
        y_w = pad
        y_b = pad + lane_h + pad
        max_len = max(len(self.w_keys), len(self.b_keys), 1)
        seg_w = max(1, (w - pad * 2) // max_len)

        x = ev.position().x()
        y = ev.position().y()
        if y_w <= y < y_w + lane_h:
            idx = int((x - pad) // seg_w)
            if 0 <= idx < len(self.w_keys):
                self.moveClicked.emit(idx, True)
        elif y_b <= y < y_b + lane_h:
            idx = int((x - pad) // seg_w)
            if 0 <= idx < len(self.b_keys):
                self.moveClicked.emit(idx, False)

    def paintEvent(self, ev):  # pragma: no cover - GUI drawing
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))

        w = self.width()
        h = self.height()
        pad = 8
        lane_h = (h - pad * 3) // 3
        y_w = pad
        y_b = pad + lane_h + pad

        # Frame of lanes
        pen_grid = QPen(QColor(230, 230, 230))
        pen_grid.setWidth(1)
        painter.setPen(pen_grid)
        painter.drawRect(QRect(pad, y_w, w - pad * 2, lane_h))
        painter.drawRect(QRect(pad, y_b, w - pad * 2, lane_h))

        # Draw tiles
        max_len = max(len(self.w_keys), len(self.b_keys), 1)
        if max_len <= 0:
            return
        seg_w = max(1, (w - pad * 2) // max_len)

        def draw_lane(keys, y):
            x = pad
            for key in keys:
                color = MODULE_COLORS.get(key, MODULE_COLORS["OTHER"])
                painter.fillRect(QRect(x, y, seg_w, lane_h), color)
                x += seg_w

        draw_lane(self.w_keys, y_w)
        draw_lane(self.b_keys, y_b)

        # Labels
        painter.setPen(QPen(QColor(60, 60, 60)))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(pad, y_w - 2, "W")
        painter.drawText(pad, y_b - 2, "B")

        # Legend (single line, truncated if not enough space)
        y_leg = y_b + lane_h + pad
        x_leg = pad
        for key in REASON_PRIORITY + ["OTHER"]:
            label = key
            rect = QRect(x_leg, y_leg, 10, 10)
            painter.fillRect(rect, MODULE_COLORS.get(key, MODULE_COLORS["OTHER"]))
            painter.setPen(QPen(QColor(80, 80, 80)))
            painter.drawRect(rect)
            painter.drawText(x_leg + 14, y_leg + 10, label)
            x_leg += 14 + painter.fontMetrics().horizontalAdvance(label) + 10
            if x_leg > w - pad * 2:
                break
