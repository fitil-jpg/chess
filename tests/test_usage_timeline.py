import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest, QSignalSpy

from ui.usage_timeline import UsageTimeline


class RecordingTimeline(UsageTimeline):
    """UsageTimeline variant that stores the last mousePressEvent result."""

    def mousePressEvent(self, ev):  # type: ignore[override]
        self.last = super().mousePressEvent(ev)
        return self.last


def _segment_pos(widget, idx: int, is_white: bool, outside: bool = False) -> QPoint:
    """Return a point inside a segment or just beyond the last segment."""
    pad = 8
    lane_h = (widget.height() - pad * 3) // 3
    max_len = max(len(widget.w_keys), len(widget.b_keys), 1)
    seg_w = max(1, (widget.width() - pad * 2) // max_len)
    y = pad + lane_h // 2 if is_white else pad + lane_h + pad + lane_h // 2
    if outside:
        x = pad + seg_w * max_len + 1
    else:
        x = pad + seg_w * idx + seg_w // 2
    return QPoint(int(x), int(y))


def test_usage_timeline_clicks_and_signal():
    app = QApplication.instance() or QApplication([])
    widget = RecordingTimeline()
    widget.resize(300, 120)
    widget.set_data(["A", "B", "C"], ["D", "E", "F"])
    widget.show()

    spy = QSignalSpy(widget.moveClicked)

    # Click second white segment
    pos_w1 = _segment_pos(widget, 1, True)
    QTest.mouseClick(widget, Qt.LeftButton, Qt.NoModifier, pos_w1)
    assert widget.last == (1, True)
    assert spy.count() == 1
    assert spy.takeFirst() == [1, True]
    spy.clear()

    # Click third black segment
    pos_b2 = _segment_pos(widget, 2, False)
    QTest.mouseClick(widget, Qt.LeftButton, Qt.NoModifier, pos_b2)
    assert widget.last == (2, False)
    assert spy.count() == 1
    assert spy.takeFirst() == [2, False]
    spy.clear()

    # Click outside any segment (right of last white segment)
    pos_out = _segment_pos(widget, 0, True, outside=True)
    QTest.mouseClick(widget, Qt.LeftButton, Qt.NoModifier, pos_out)
    assert widget.last is None
    assert spy.count() == 0

    widget.close()
