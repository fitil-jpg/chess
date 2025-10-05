from __future__ import annotations

from typing import Dict, Any, Optional

from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget


class DebugPanel(QWidget):
    """Minimal debug overlay to show evaluator metrics.

    Embed this widget in an existing layout.  Call ``update_metrics(data)`` on
    each move to refresh the displayed values.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        self._title = QLabel("AI Metrics")
        self._layout.addWidget(self._title)
        self._rows: Dict[str, QLabel] = {}

    def update_metrics(self, metrics: Optional[Dict[str, Any]]) -> None:
        # Remove old labels
        for lbl in self._rows.values():
            self._layout.removeWidget(lbl)
            lbl.deleteLater()
        self._rows.clear()

        if not metrics:
            self._layout.addWidget(QLabel("(no metrics)"))
            return

        for key, value in sorted(metrics.items()):
            row = QLabel(f"{key}: {value}")
            self._layout.addWidget(row)
            self._rows[key] = row
