"""
Method Status Widget

Displays the status of all evaluation methods in the move pipeline,
showing which methods are active, their values, and current processing status.
"""

import logging
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from core.move_object import MoveObject, MethodStatus, MethodResult

logger = logging.getLogger(__name__)


class MethodStatusItem(QFrame):
    """Single method status display item."""

    def __init__(self, method_result: MethodResult, parent=None):
        super().__init__(parent)
        self.method_result = method_result
        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI for this status item."""
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Method name and status
        header_layout = QHBoxLayout()

        # Status icon
        status_icon = self._get_status_icon()
        status_label = QLabel(status_icon)
        status_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(status_label)

        # Method name
        name_label = QLabel(f"<b>{self.method_result.method_name}</b>")
        name_label.setStyleSheet("font-size: 11px;")
        header_layout.addWidget(name_label)

        header_layout.addStretch()

        # Active indicator
        if self.method_result.active_in_board:
            active_label = QLabel("🟢 ACTIVE")
            active_label.setStyleSheet("color: green; font-size: 10px; font-weight: bold;")
            header_layout.addWidget(active_label)

        layout.addLayout(header_layout)

        # Value and metadata
        details_layout = QHBoxLayout()

        # Value
        if self.method_result.value is not None:
            value_label = QLabel(f"Value: {self.method_result.value:.3f}")
            value_label.setStyleSheet("font-size: 10px; color: #495057;")
            details_layout.addWidget(value_label)

        # Processing time
        if self.method_result.processing_time_ms > 0:
            time_label = QLabel(f"⏱ {self.method_result.processing_time_ms:.1f}ms")
            time_label.setStyleSheet("font-size: 9px; color: #6c757d;")
            details_layout.addWidget(time_label)

        details_layout.addStretch()
        layout.addLayout(details_layout)

        # Metadata (if any)
        if self.method_result.metadata:
            metadata_text = ", ".join(f"{k}={v}" for k, v in self.method_result.metadata.items())
            if len(metadata_text) > 100:
                metadata_text = metadata_text[:97] + "..."
            metadata_label = QLabel(metadata_text)
            metadata_label.setStyleSheet("font-size: 9px; color: #868e96; font-style: italic;")
            metadata_label.setWordWrap(True)
            layout.addWidget(metadata_label)

    def _get_status_icon(self) -> str:
        """Get the icon for the current status."""
        status_icons = {
            MethodStatus.PENDING: "⏳",
            MethodStatus.PROCESSING: "⚙️",
            MethodStatus.COMPLETED: "✅",
            MethodStatus.SKIPPED: "⏭️",
            MethodStatus.FAILED: "❌"
        }
        return status_icons.get(self.method_result.status, "❓")


class MethodStatusWidget(QWidget):
    """
    Widget displaying all method statuses for the current move evaluation.

    Shows which methods are:
    - Active (DA/YES) - applies to current board
    - Processing, Completed, Skipped, or Failed
    - What value each method computed
    - Processing time for each method
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_move: Optional[MoveObject] = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title_layout = QHBoxLayout()
        title = QLabel("📊 Method Status Pipeline")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        title_layout.addWidget(title)

        # Filter toggle (show only active methods)
        self.filter_active_only = False
        self.filter_button = QLabel("[ Show Only Active ]")
        self.filter_button.setStyleSheet("""
            QLabel {
                color: #007bff;
                text-decoration: underline;
                cursor: pointer;
                font-size: 10px;
            }
        """)
        self.filter_button.mousePressEvent = self._toggle_filter
        title_layout.addWidget(self.filter_button)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Summary stats
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                border-radius: 3px;
                padding: 5px;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.summary_label)

        # Scroll area for method status items
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8f9fa;
            }
        """)

        # Container for status items
        self.status_container = QWidget()
        self.status_layout = QVBoxLayout(self.status_container)
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.addStretch()

        scroll_area.setWidget(self.status_container)
        layout.addWidget(scroll_area)

        self._update_display()

    def set_move(self, move_obj: MoveObject):
        """Set the current move to display status for."""
        self.current_move = move_obj
        self._update_display()

    def clear(self):
        """Clear all displayed status items."""
        self.current_move = None
        self._update_display()

    def _toggle_filter(self, event):
        """Toggle the active-only filter."""
        self.filter_active_only = not self.filter_active_only
        if self.filter_active_only:
            self.filter_button.setText("[ Show All ]")
        else:
            self.filter_button.setText("[ Show Only Active ]")
        self._update_display()

    def _update_display(self):
        """Update the display with current move status."""
        # Clear existing items
        while self.status_layout.count() > 1:  # Keep the stretch
            item = self.status_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.current_move:
            self.summary_label.setText("No move being evaluated")
            return

        # Update summary
        self._update_summary()

        # Get method results to display
        results = list(self.current_move.method_results.values())
        if self.filter_active_only:
            results = [r for r in results if r.active_in_board]

        # Sort by status priority and name
        status_priority = {
            MethodStatus.PROCESSING: 0,
            MethodStatus.PENDING: 1,
            MethodStatus.COMPLETED: 2,
            MethodStatus.SKIPPED: 3,
            MethodStatus.FAILED: 4
        }
        results.sort(key=lambda r: (status_priority.get(r.status, 99), r.method_name))

        # Add status items
        for result in results:
            item = MethodStatusItem(result)
            self.status_layout.insertWidget(self.status_layout.count() - 1, item)

        # If no results, show message
        if not results:
            no_results_label = QLabel("No method results to display")
            no_results_label.setStyleSheet("color: #6c757d; font-style: italic; padding: 20px;")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.status_layout.insertWidget(0, no_results_label)

    def _update_summary(self):
        """Update the summary statistics."""
        if not self.current_move:
            return

        results = list(self.current_move.method_results.values())

        # Count by status
        status_counts = {
            MethodStatus.PENDING: 0,
            MethodStatus.PROCESSING: 0,
            MethodStatus.COMPLETED: 0,
            MethodStatus.SKIPPED: 0,
            MethodStatus.FAILED: 0
        }

        active_count = 0
        total_time = 0.0

        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
            if result.active_in_board:
                active_count += 1
            total_time += result.processing_time_ms

        # Build summary text
        parts = []
        parts.append(f"<b>Move:</b> {self.current_move.move.uci()}")
        parts.append(f"<b>Stage:</b> {self.current_move.current_stage.value}")
        parts.append(f"<b>Total Methods:</b> {len(results)}")
        parts.append(f"<b>Active:</b> {active_count}")

        status_text = []
        for status, count in status_counts.items():
            if count > 0:
                icon = {
                    MethodStatus.PENDING: "⏳",
                    MethodStatus.PROCESSING: "⚙️",
                    MethodStatus.COMPLETED: "✅",
                    MethodStatus.SKIPPED: "⏭️",
                    MethodStatus.FAILED: "❌"
                }.get(status, "❓")
                status_text.append(f"{icon}×{count}")

        if status_text:
            parts.append("<b>Status:</b> " + " ".join(status_text))

        if total_time > 0:
            parts.append(f"<b>Total Time:</b> {total_time:.1f}ms")

        self.summary_label.setText(" | ".join(parts))


__all__ = ["MethodStatusWidget", "MethodStatusItem"]
