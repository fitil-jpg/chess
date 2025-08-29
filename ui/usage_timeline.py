"""Timeline widget visualising per-move module usage.

Two horizontal lanes represent White (top) and Black (bottom).
Each move is drawn as a coloured rectangle according to the module
that produced it.  Clicking on a rectangle emits the corresponding
move index and colour side.
"""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QPen, QFont, QColor, QMouseEvent
from PySide6.QtWidgets import QWidget

from utils.module_colors import MODULE_COLORS, REASON_PRIORITY

__all__ = ["UsageTimeline"]


class UsageTimeline(QWidget):
    """Simple timeline: two rows of tiles (White on top, Black below)."""

    moveClicked = Signal(int, bool)  # index, is_white

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.w_keys: list[str] = []  # list of module keys per White move
        self.b_keys: list[str] = []  # list of module keys per Black move
        self._selected: tuple[int, bool] | None = None
        self._hover: tuple[int, bool] | None = None
        self.setMouseTracking(True)
        self.setMinimumSize(280, 120)

    def set_data(self, w_keys: list[str], b_keys: list[str]) -> None:
        self.w_keys = list(w_keys)
        self.b_keys = list(b_keys)
        self._selected = None
        self._hover = None
        self.update()

    def set_selected(self, idx: int | None, is_white: bool | None = None) -> None:
        """Highlight ``(idx, is_white)`` or clear when ``idx`` is ``None``."""
        if idx is None:
            self._selected = None
        else:
            assert is_white is not None
            self._selected = (idx, is_white)
        self.update()

    def mousePressEvent(self, ev: QMouseEvent) -> tuple[int, bool] | None:  # pragma: no cover - UI interaction
        """Emit the index and side of a clicked move.

        The method also returns a tuple ``(index, is_white)`` for convenience
        which eases unit testing and direct invocation.  ``None`` is returned
        when the click does not correspond to a move tile.
        """

        if ev.button() != Qt.LeftButton:
            return None

        # Geometry of the two lanes
        w = self.width()
        h = self.height()
        pad = 8
        lane_h = (h - pad * 3) // 3
        y_w = pad
        y_b = pad + lane_h + pad
        max_len = max(len(self.w_keys), len(self.b_keys), 1)
        seg_w = max(1, (w - pad * 2) // max_len)

        # ``QMouseEvent.position`` is available in Qt6; fall back to ``pos``
        # for older Qt versions.  Coordinates are extracted in float to avoid
        # rounding issues when calculating the tile index.
        pos = ev.position() if hasattr(ev, "position") else ev.pos()
        x, y = pos.x(), pos.y()

        is_white: bool | None
        keys: list[str]
        if y_w <= y < y_w + lane_h:
            is_white, keys = True, self.w_keys
        elif y_b <= y < y_b + lane_h:
            is_white, keys = False, self.b_keys
        else:
            return None

        idx = int((x - pad) // seg_w)
        if 0 <= idx < len(keys):
            self.set_selected(idx, is_white)
            self.moveClicked.emit(idx, is_white)
            return idx, is_white
        return None

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:  # pragma: no cover - UI interaction
        """Track which tile is under the cursor and trigger a repaint."""

        # Geometry of the two lanes (same as ``mousePressEvent``)
        w = self.width()
        h = self.height()
        pad = 8
        lane_h = (h - pad * 3) // 3
        y_w = pad
        y_b = pad + lane_h + pad
        max_len = max(len(self.w_keys), len(self.b_keys), 1)
        seg_w = max(1, (w - pad * 2) // max_len)

        pos = ev.position() if hasattr(ev, "position") else ev.pos()
        x, y = pos.x(), pos.y()

        is_white: bool | None
        keys: list[str]
        if y_w <= y < y_w + lane_h:
            is_white, keys = True, self.w_keys
        elif y_b <= y < y_b + lane_h:
            is_white, keys = False, self.b_keys
        else:
            if self._hover is not None:
                self._hover = None
                self.update()
            return

        idx = int((x - pad) // seg_w)
        new_hover = (idx, is_white) if 0 <= idx < len(keys) else None
        if new_hover != self._hover:
            self._hover = new_hover
            self.update()

    def leaveEvent(self, ev):  # pragma: no cover - UI interaction
        if self._hover is not None:
            self._hover = None
            self.update()
        super().leaveEvent(ev)

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

        painter.setPen(Qt.NoPen)

        def draw_lane(keys, y, is_white):
            x = pad
            for i, key in enumerate(keys):
                rect = QRect(x, y, seg_w, lane_h)
                color = MODULE_COLORS.get(key, MODULE_COLORS["OTHER"])
                painter.fillRect(rect, color)
                if self._hover == (i, is_white):
                    painter.save()
                    painter.setPen(Qt.NoPen)
                    painter.fillRect(rect, QColor(0, 0, 0, 40))
                    painter.restore()
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.drawLine(x + seg_w, y, x + seg_w, y + lane_h)
                painter.setPen(Qt.NoPen)
                if self._selected == (i, is_white):
                    painter.save()
                    pen_sel = QPen(QColor(0, 0, 0))
                    pen_sel.setWidth(2)
                    painter.setPen(pen_sel)
                    painter.drawRect(rect)
                    painter.restore()
                x += seg_w

        draw_lane(self.w_keys, y_w, True)
        draw_lane(self.b_keys, y_b, False)

        # Move number labels between the two lanes
        painter.setPen(QPen(QColor(60, 60, 60)))
        num_font = QFont()
        num_font.setPointSize(8)
        painter.setFont(num_font)
        fm = painter.fontMetrics()
        y_num = y_w + lane_h + pad // 2 + fm.ascent() // 2
        min_width = fm.horizontalAdvance(str(max_len)) + 2
        step = max(1, math.ceil(min_width / seg_w))
        for i in range(0, max_len, step):
            label = str(i + 1)
            x = pad + seg_w * i
            text_x = x + seg_w // 2 - fm.horizontalAdvance(label) // 2
            painter.drawText(text_x, y_num, label)

        # Secondary bar showing per-move module usage
        bar_keys: list[str] = []
        for i in range(max_len):
            if i < len(self.w_keys):
                bar_keys.append(self.w_keys[i])
            if i < len(self.b_keys):
                bar_keys.append(self.b_keys[i])

        bar_h = max(2, pad // 2)
        if bar_keys:
            y_bar = y_b + lane_h + 2
            seg_bar = max(1, (w - pad * 2) // len(bar_keys))
            x = pad
            for key in bar_keys:
                color = MODULE_COLORS.get(key, MODULE_COLORS["OTHER"])
                painter.fillRect(QRect(x, y_bar, seg_bar, bar_h), color)
                x += seg_bar

        # Labels
        painter.setPen(QPen(QColor(60, 60, 60)))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(pad, y_w - 2, "W")
        painter.drawText(pad, y_b - 2, "B")

        # Legend (single line, truncated if not enough space)
        y_leg = y_b + lane_h + pad + bar_h + 4
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
