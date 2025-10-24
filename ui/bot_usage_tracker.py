"""
Bot Usage Statistics and Method Tracking Widget.

This module provides comprehensive tracking and visualization of bot usage
statistics, method performance, and evaluation metrics in the PySide viewer.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QProgressBar, QPushButton, QComboBox, QCheckBox,
    QScrollArea, QFrame, QGridLayout, QSplitter
)
from PySide6.QtCore import Qt, QTimer, pyqtSignal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
import chess

from core.move_object import move_evaluation_manager, MoveEvaluation, MoveStatus
from core.move_evaluator import enhanced_move_evaluator


@dataclass
class BotUsageStats:
    """Statistics for a single bot."""
    name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    confidence_sum: float = 0.0
    avg_confidence: float = 0.0
    last_used: Optional[float] = None
    methods_used: Dict[str, int] = None
    
    def __post_init__(self):
        if self.methods_used is None:
            self.methods_used = defaultdict(int)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    def update_stats(self, duration_ms: float, confidence: float, 
                    method_name: str, success: bool) -> None:
        """Update statistics with new data."""
        self.total_calls += 1
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.total_calls
        
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        self.confidence_sum += confidence
        self.avg_confidence = self.confidence_sum / self.total_calls
        
        self.last_used = time.time()
        self.methods_used[method_name] += 1


class BotPerformanceChart(QWidget):
    """Chart widget showing bot performance over time."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.colors = {
            'success_rate': QColor(0, 255, 0),
            'avg_duration': QColor(0, 0, 255),
            'avg_confidence': QColor(255, 165, 0),
            'call_frequency': QColor(255, 0, 255)
        }
        self.setMinimumHeight(200)
        self.setMinimumWidth(400)
    
    def add_data_point(self, bot_name: str, metric: str, value: float, timestamp: float) -> None:
        """Add a data point for visualization."""
        if bot_name not in self.data_points:
            self.data_points[bot_name] = defaultdict(lambda: deque(maxlen=50))
        
        self.data_points[bot_name][metric].append((timestamp, value))
        self.update()
    
    def paintEvent(self, event):
        """Paint the performance chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        
        # Draw grid
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        width, height = self.width(), self.height()
        
        # Vertical grid lines
        for i in range(0, width, 50):
            painter.drawLine(i, 0, i, height)
        
        # Horizontal grid lines
        for i in range(0, height, 25):
            painter.drawLine(0, i, width, i)
        
        # Draw data lines
        if not self.data_points:
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "No performance data available")
            return
        
        # Draw legend
        legend_y = 20
        painter.setFont(QFont("Arial", 10))
        for metric, color in self.colors.items():
            painter.setPen(QPen(color, 2))
            painter.drawLine(10, legend_y, 30, legend_y)
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(35, legend_y + 5, metric.replace('_', ' ').title())
            legend_y += 20
        
        # Draw performance lines for each bot
        for bot_name, bot_data in self.data_points.items():
            for metric, points in bot_data.items():
                if len(points) < 2:
                    continue
                
                color = self.colors.get(metric, QColor(128, 128, 128))
                painter.setPen(QPen(color, 2))
                
                # Convert data points to screen coordinates
                if points:
                    min_time = min(p[0] for p in points)
                    max_time = max(p[0] for p in points)
                    min_value = min(p[1] for p in points)
                    max_value = max(p[1] for p in points)
                    
                    if max_time > min_time and max_value > min_value:
                        prev_x, prev_y = None, None
                        for timestamp, value in points:
                            x = int((timestamp - min_time) / (max_time - min_time) * (width - 100)) + 50
                            y = int(height - 50 - (value - min_value) / (max_value - min_value) * (height - 100))
                            
                            if prev_x is not None and prev_y is not None:
                                painter.drawLine(prev_x, prev_y, x, y)
                            
                            prev_x, prev_y = x, y


class MethodUsageTable(QTableWidget):
    """Table showing method usage statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Method", "Bot", "Calls", "Success Rate", "Avg Duration (ms)", "Avg Confidence"
        ])
        self.setSortingEnabled(True)
        self.method_stats: Dict[Tuple[str, str], Dict[str, Any]] = {}
    
    def update_method_stats(self, method_name: str, bot_name: str, 
                           duration_ms: float, confidence: float, success: bool) -> None:
        """Update method statistics."""
        key = (method_name, bot_name)
        
        if key not in self.method_stats:
            self.method_stats[key] = {
                'calls': 0,
                'successes': 0,
                'total_duration': 0.0,
                'total_confidence': 0.0
            }
        
        stats = self.method_stats[key]
        stats['calls'] += 1
        stats['total_duration'] += duration_ms
        stats['total_confidence'] += confidence
        
        if success:
            stats['successes'] += 1
        
        self._refresh_table()
    
    def _refresh_table(self) -> None:
        """Refresh the table display."""
        self.setRowCount(len(self.method_stats))
        
        for row, ((method_name, bot_name), stats) in enumerate(self.method_stats.items()):
            # Method name
            self.setItem(row, 0, QTableWidgetItem(method_name))
            
            # Bot name
            self.setItem(row, 1, QTableWidgetItem(bot_name))
            
            # Calls
            self.setItem(row, 2, QTableWidgetItem(str(stats['calls'])))
            
            # Success rate
            success_rate = stats['successes'] / stats['calls'] if stats['calls'] > 0 else 0.0
            self.setItem(row, 3, QTableWidgetItem(f"{success_rate:.2%}"))
            
            # Average duration
            avg_duration = stats['total_duration'] / stats['calls'] if stats['calls'] > 0 else 0.0
            self.setItem(row, 4, QTableWidgetItem(f"{avg_duration:.1f}"))
            
            # Average confidence
            avg_confidence = stats['total_confidence'] / stats['calls'] if stats['calls'] > 0 else 0.0
            self.setItem(row, 5, QTableWidgetItem(f"{avg_confidence:.2f}"))
        
        self.resizeColumnsToContents()


class BotUsageTracker(QWidget):
    """Main widget for tracking and displaying bot usage statistics."""
    
    # Signals
    stats_updated = pyqtSignal(dict)
    bot_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data storage
        self.bot_stats: Dict[str, BotUsageStats] = {}
        self.recent_evaluations: deque = deque(maxlen=100)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_displays)
        self.update_timer.start(1000)  # Update every second
        
        # UI components
        self.performance_chart: Optional[BotPerformanceChart] = None
        self.method_table: Optional[MethodUsageTable] = None
        self.bot_summary_labels: Dict[str, QLabel] = {}
        
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Bot Usage Statistics & Method Tracking")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Auto-update checkbox
        self.auto_update_checkbox = QCheckBox("Auto Update")
        self.auto_update_checkbox.setChecked(True)
        self.auto_update_checkbox.toggled.connect(self._on_auto_update_toggled)
        controls_layout.addWidget(self.auto_update_checkbox)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._refresh_all_data)
        controls_layout.addWidget(refresh_button)
        
        # Clear stats button
        clear_button = QPushButton("Clear Stats")
        clear_button.clicked.connect(self._clear_statistics)
        controls_layout.addWidget(clear_button)
        
        # Export button
        export_button = QPushButton("Export Data")
        export_button.clicked.connect(self._export_statistics)
        controls_layout.addWidget(export_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Main content tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Bot Summary Tab
        self._setup_bot_summary_tab()
        
        # Performance Chart Tab
        self._setup_performance_chart_tab()
        
        # Method Usage Tab
        self._setup_method_usage_tab()
        
        # Recent Activity Tab
        self._setup_recent_activity_tab()
    
    def _setup_bot_summary_tab(self) -> None:
        """Set up the bot summary tab."""
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        # Bot statistics grid
        self.bot_grid_frame = QFrame()
        self.bot_grid_layout = QGridLayout(self.bot_grid_frame)
        
        summary_layout.addWidget(QLabel("Bot Performance Summary:"))
        summary_layout.addWidget(self.bot_grid_frame)
        summary_layout.addStretch()
        
        self.tab_widget.addTab(summary_widget, "📊 Bot Summary")
    
    def _setup_performance_chart_tab(self) -> None:
        """Set up the performance chart tab."""
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        # Chart controls
        chart_controls = QHBoxLayout()
        chart_controls.addWidget(QLabel("Metric:"))
        
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(["success_rate", "avg_duration", "avg_confidence", "call_frequency"])
        chart_controls.addWidget(self.metric_combo)
        
        chart_controls.addStretch()
        chart_layout.addLayout(chart_controls)
        
        # Performance chart
        self.performance_chart = BotPerformanceChart()
        chart_layout.addWidget(self.performance_chart)
        
        self.tab_widget.addTab(chart_widget, "📈 Performance")
    
    def _setup_method_usage_tab(self) -> None:
        """Set up the method usage tab."""
        method_widget = QWidget()
        method_layout = QVBoxLayout(method_widget)
        
        method_layout.addWidget(QLabel("Method Usage Statistics:"))
        
        # Method usage table
        self.method_table = MethodUsageTable()
        method_layout.addWidget(self.method_table)
        
        self.tab_widget.addTab(method_widget, "🔧 Methods")
    
    def _setup_recent_activity_tab(self) -> None:
        """Set up the recent activity tab."""
        activity_widget = QWidget()
        activity_layout = QVBoxLayout(activity_widget)
        
        activity_layout.addWidget(QLabel("Recent Evaluation Activity:"))
        
        # Recent activity log
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(300)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        activity_layout.addWidget(self.activity_log)
        
        self.tab_widget.addTab(activity_widget, "📝 Activity")
    
    def _start_monitoring(self) -> None:
        """Start monitoring move evaluations."""
        # This would connect to the move evaluation manager
        # For now, we'll simulate with a timer
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self._check_for_new_evaluations)
        self.monitoring_timer.start(500)  # Check every 500ms
    
    def _check_for_new_evaluations(self) -> None:
        """Check for new move evaluations."""
        # Get recent evaluations from the move evaluation manager
        recent_moves = move_evaluation_manager.get_recent_moves(10)
        
        for move_eval in recent_moves:
            if move_eval not in self.recent_evaluations:
                self._process_new_evaluation(move_eval)
                self.recent_evaluations.append(move_eval)
    
    def _process_new_evaluation(self, move_eval: MoveEvaluation) -> None:
        """Process a new move evaluation."""
        # Update bot statistics
        for step in move_eval.evaluation_steps:
            if step.bot_name:
                self._update_bot_stats(step.bot_name, step)
        
        # Add to activity log
        self._add_to_activity_log(move_eval)
        
        # Update performance chart
        if self.performance_chart:
            for bot_name in move_eval.get_active_bots():
                if bot_name in self.bot_stats:
                    stats = self.bot_stats[bot_name]
                    timestamp = time.time()
                    
                    self.performance_chart.add_data_point(
                        bot_name, "success_rate", stats.success_rate, timestamp
                    )
                    self.performance_chart.add_data_point(
                        bot_name, "avg_duration", stats.avg_duration_ms, timestamp
                    )
                    self.performance_chart.add_data_point(
                        bot_name, "avg_confidence", stats.avg_confidence, timestamp
                    )
    
    def _update_bot_stats(self, bot_name: str, step) -> None:
        """Update statistics for a specific bot."""
        if bot_name not in self.bot_stats:
            self.bot_stats[bot_name] = BotUsageStats(name=bot_name)
        
        stats = self.bot_stats[bot_name]
        success = step.status == MoveStatus.COMPLETED
        
        stats.update_stats(
            duration_ms=step.duration_ms,
            confidence=step.confidence,
            method_name=step.method_name,
            success=success
        )
        
        # Update method table
        if self.method_table:
            self.method_table.update_method_stats(
                step.method_name, bot_name, step.duration_ms, step.confidence, success
            )
    
    def _add_to_activity_log(self, move_eval: MoveEvaluation) -> None:
        """Add move evaluation to activity log."""
        if not self.activity_log:
            return
        
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        move_info = move_eval.san_notation or str(move_eval.move)
        
        log_entry = f"[{timestamp}] {move_info} - "
        log_entry += f"Score: {move_eval.final_score:.1f}, "
        log_entry += f"Confidence: {move_eval.confidence:.2f}, "
        log_entry += f"Reason: {move_eval.primary_reason}, "
        log_entry += f"Duration: {move_eval.total_duration_ms:.1f}ms"
        
        if move_eval.get_active_bots():
            log_entry += f", Bots: {', '.join(move_eval.get_active_bots())}"
        
        self.activity_log.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _update_displays(self) -> None:
        """Update all display components."""
        if not self.auto_update_checkbox.isChecked():
            return
        
        self._update_bot_summary_display()
    
    def _update_bot_summary_display(self) -> None:
        """Update the bot summary display."""
        # Clear existing labels
        for label in self.bot_summary_labels.values():
            label.deleteLater()
        self.bot_summary_labels.clear()
        
        # Add updated labels
        row = 0
        for bot_name, stats in self.bot_stats.items():
            # Bot name
            name_label = QLabel(f"<b>{bot_name}</b>")
            self.bot_grid_layout.addWidget(name_label, row, 0)
            
            # Calls
            calls_label = QLabel(f"Calls: {stats.total_calls}")
            self.bot_grid_layout.addWidget(calls_label, row, 1)
            
            # Success rate
            success_label = QLabel(f"Success: {stats.success_rate:.1%}")
            self.bot_grid_layout.addWidget(success_label, row, 2)
            
            # Average duration
            duration_label = QLabel(f"Avg Duration: {stats.avg_duration_ms:.1f}ms")
            self.bot_grid_layout.addWidget(duration_label, row, 3)
            
            # Average confidence
            confidence_label = QLabel(f"Avg Confidence: {stats.avg_confidence:.2f}")
            self.bot_grid_layout.addWidget(confidence_label, row, 4)
            
            # Last used
            if stats.last_used:
                last_used_str = time.strftime("%H:%M:%S", time.localtime(stats.last_used))
                last_used_label = QLabel(f"Last Used: {last_used_str}")
            else:
                last_used_label = QLabel("Last Used: Never")
            self.bot_grid_layout.addWidget(last_used_label, row, 5)
            
            # Store labels for cleanup
            self.bot_summary_labels[f"{bot_name}_name"] = name_label
            self.bot_summary_labels[f"{bot_name}_calls"] = calls_label
            self.bot_summary_labels[f"{bot_name}_success"] = success_label
            self.bot_summary_labels[f"{bot_name}_duration"] = duration_label
            self.bot_summary_labels[f"{bot_name}_confidence"] = confidence_label
            self.bot_summary_labels[f"{bot_name}_last_used"] = last_used_label
            
            row += 1
    
    def _on_auto_update_toggled(self, checked: bool) -> None:
        """Handle auto-update toggle."""
        if checked:
            self.update_timer.start(1000)
        else:
            self.update_timer.stop()
    
    def _refresh_all_data(self) -> None:
        """Refresh all data displays."""
        self._update_displays()
        if self.performance_chart:
            self.performance_chart.update()
        if self.method_table:
            self.method_table._refresh_table()
    
    def _clear_statistics(self) -> None:
        """Clear all statistics."""
        self.bot_stats.clear()
        self.recent_evaluations.clear()
        
        if self.method_table:
            self.method_table.method_stats.clear()
            self.method_table.setRowCount(0)
        
        if self.activity_log:
            self.activity_log.clear()
        
        if self.performance_chart:
            self.performance_chart.data_points.clear()
            self.performance_chart.update()
        
        self._update_displays()
    
    def _export_statistics(self) -> None:
        """Export statistics to a file."""
        import json
        from PySide6.QtWidgets import QFileDialog
        
        # Prepare data for export
        export_data = {
            'timestamp': time.time(),
            'bot_stats': {},
            'method_stats': {},
            'recent_evaluations': []
        }
        
        # Bot statistics
        for bot_name, stats in self.bot_stats.items():
            export_data['bot_stats'][bot_name] = {
                'total_calls': stats.total_calls,
                'successful_calls': stats.successful_calls,
                'failed_calls': stats.failed_calls,
                'success_rate': stats.success_rate,
                'avg_duration_ms': stats.avg_duration_ms,
                'avg_confidence': stats.avg_confidence,
                'methods_used': dict(stats.methods_used)
            }
        
        # Method statistics
        if self.method_table:
            for (method_name, bot_name), stats in self.method_table.method_stats.items():
                key = f"{method_name}_{bot_name}"
                export_data['method_stats'][key] = stats
        
        # Recent evaluations
        for move_eval in list(self.recent_evaluations)[-20:]:  # Last 20 evaluations
            export_data['recent_evaluations'].append(move_eval.get_evaluation_summary())
        
        # Save to file
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Bot Statistics", "bot_stats.json", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                if self.activity_log:
                    self.activity_log.append(f"Statistics exported to {file_path}")
            except Exception as e:
                if self.activity_log:
                    self.activity_log.append(f"Export failed: {e}")
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get a summary of current statistics."""
        return {
            'total_bots': len(self.bot_stats),
            'total_evaluations': len(self.recent_evaluations),
            'bot_stats': {name: {
                'calls': stats.total_calls,
                'success_rate': stats.success_rate,
                'avg_duration_ms': stats.avg_duration_ms,
                'avg_confidence': stats.avg_confidence
            } for name, stats in self.bot_stats.items()},
            'method_count': len(self.method_table.method_stats) if self.method_table else 0
        }