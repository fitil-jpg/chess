from __future__ import annotations

"""Simple timeline widget with tick marks and move number labels."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget

__all__ = ["Timeline"]


class Timeline(QWidget):
    """Horizontal timeline showing a tick for each move.

    Parameters
    ----------
    label_interval:
        Base interval between labelled ticks.  If the widget is too
        narrow to show labels at this interval, a larger multiple is
        automatically chosen.
    """

    def __init__(self, parent: QWidget | None = None, label_interval: int = 5) -> None:
        super().__init__(parent)
        self.move_count = 0
        self.label_interval = max(1, int(label_interval))
        self.setMinimumHeight(24)

    def set_move_count(self, count: int) -> None:
        """Set the number of moves represented by the timeline."""

        self.move_count = max(0, int(count))
        self.update()

    @staticmethod
    def _compute_label_step(seg_w: float, base_step: int, max_label_width: int) -> int:
        """Return a multiple of ``base_step`` providing enough label spacing."""

        if base_step <= 0:
            return 1
        min_spacing = max_label_width + 4  # extra padding between numbers
        step = max(base_step, 1)
        if seg_w <= 0:
            return step
        while seg_w * step < min_spacing:
            step += base_step
        return step

    # ------------------------------------------------------------------
    def paintEvent(self, ev):  # pragma: no cover - GUI drawing
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)

        if self.move_count <= 0:
            return

        w = self.width()
        h = self.height()
        pad = 8
        tick_h = 4
        baseline_y = h - pad - tick_h

        seg_w = (w - pad * 2) / self.move_count if self.move_count else 0

        font = QFont()
        painter.setFont(font)
        fm = painter.fontMetrics()
        max_label_width = fm.horizontalAdvance(str(self.move_count))
        label_step = self._compute_label_step(seg_w, self.label_interval, max_label_width)

        pen = QPen(Qt.black)
        painter.setPen(pen)

        for i in range(self.move_count):
            x = pad + i * seg_w
            painter.drawLine(int(x), baseline_y, int(x), baseline_y + tick_h)
            draw_label = i == 0 or (i + 1) % label_step == 0
            if draw_label:
                text = str(i + 1)
                tw = fm.horizontalAdvance(text)
                painter.drawText(int(x - tw / 2), baseline_y + tick_h + fm.ascent() + 2, text)

