import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from ui.timeline import Timeline


def test_compute_label_step():
    # plenty of space -> no adjustment
    assert Timeline._compute_label_step(seg_w=10, base_step=5, max_label_width=10) == 5
    # insufficient space -> step increases
    assert Timeline._compute_label_step(seg_w=2, base_step=5, max_label_width=10) == 10
    assert Timeline._compute_label_step(seg_w=1, base_step=5, max_label_width=10) == 15
