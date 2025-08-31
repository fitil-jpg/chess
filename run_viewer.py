from utils.usage_logger import record_usage, read_usage
record_usage(__file__)

import os
import sys
import chess
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Signal, Qt
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QValueAxis,
    QBarCategoryAxis,
)

from ui.mini_board import MiniBoard
from ui.usage_timeline import UsageTimeline
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage
from utils.module_colors import MODULE_COLORS


class OverallUsageChart(QChartView):
    """Bar chart summarising module usage across multiple runs."""

    moduleClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._series = QBarSeries()
        chart = QChart()
        chart.addSeries(self._series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        self.setChart(chart)
        self.setRenderHint(QPainter.Antialiasing)
        self._selected: str | None = None
        self._sets: dict[QBarSet, tuple[str, QColor]] = {}
        self.setMinimumHeight(220)

    def set_data(self, counts):
        """Populate the chart with module usage *counts*."""
        chart = self.chart()
        chart.removeSeries(self._series)
        self._series = QBarSeries()
        self._sets.clear()

        for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            bar = QBarSet(f"{name} ({count})")
            bar.append(count)
            color = MODULE_COLORS.get(name, MODULE_COLORS["OTHER"])
            bar.setColor(color)
            bar.clicked.connect(lambda _, n=name: self.moduleClicked.emit(n))
            self._series.append(bar)
            self._sets[bar] = (name, color)

        chart.addSeries(self._series)
        axis_x = QBarCategoryAxis()
        axis_x.append([""])
        chart.addAxis(axis_x, Qt.AlignBottom)
        self._series.attachAxis(axis_x)

        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        self._series.attachAxis(axis_y)
        axis_y.applyNiceNumbers()

        self.set_selected(self._selected)

    def set_selected(self, name: str | None) -> None:
        """Highlight *name* in the chart (or clear with ``None``)."""
        self._selected = name
        for bar, (mod, color) in self._sets.items():
            if name and mod != name:
                bar.setColor(color.lighter(160))
            else:
                bar.setColor(color)


class UsageTable(QTableWidget):
    """Table listing file usage counts."""

    def __init__(self, parent=None):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["File", "Count"])
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)

    def set_data(self, usage: dict[str, int]) -> None:
        self.setRowCount(len(usage))
        for row, (path, count) in enumerate(
            sorted(usage.items(), key=lambda kv: (-kv[1], kv[0]))
        ):
            self.setItem(row, 0, QTableWidgetItem(os.path.basename(path)))
            self.setItem(row, 1, QTableWidgetItem(str(count)))
        self.resizeColumnsToContents()


class RunViewer(QWidget):
    """Simple dashboard for inspecting recorded bot runs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Run Viewer")
        self.all_runs = load_runs("runs")
        self.runs = list(self.all_runs)
        self.current_run = None
        self.active_module = None

        # --- Left panel: list of run files ---
        self.run_list = QListWidget()
        for run in self.runs:
            result: str | None = run.get("result")
            game_id = run.get("game_id", "<unknown>")
            label = (
                f"{game_id} ({result})"
                if result and result != "*"
                else game_id
            )
            self.run_list.addItem(label)
        self.run_list.currentRowChanged.connect(self._on_run_selected)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_runs)

        left = QVBoxLayout()
        left.addWidget(self.run_list)
        left.addWidget(self.refresh_btn)

        # --- Centre: usage timeline ---
        self.timeline = UsageTimeline()
        self.timeline.moveClicked.connect(self._on_timeline_click)

        centre = QVBoxLayout()
        centre.addWidget(QLabel("Usage timeline"))
        centre.addWidget(self.timeline)

        # --- Right: mini board and moves list ---
        self.board = MiniBoard(scale=0.5)
        self.moves = QListWidget()
        right = QVBoxLayout()
        right.addWidget(self.board)
        right.addWidget(QLabel("Moves"))
        right.addWidget(self.moves)

        # --- Assemble top layout ---
        top = QHBoxLayout()
        top.addLayout(left)
        top.addLayout(centre)
        top.addLayout(right)

        # --- Bottom: overall usage chart ---
        self.overall_chart = OverallUsageChart()
        self.overall_chart.set_data(aggregate_module_usage(self.all_runs))
        self.overall_chart.moduleClicked.connect(self._on_overall_module_click)

        chart_scroll = QScrollArea()
        chart_scroll.setWidgetResizable(True)
        chart_scroll.setWidget(self.overall_chart)

        self.usage_table = UsageTable()
        self.usage_table.set_data(read_usage())

        bottom = QHBoxLayout()
        bottom.addWidget(chart_scroll)
        bottom.addWidget(self.usage_table)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(bottom)

        if self.runs:
            self.run_list.setCurrentRow(0)

    # --------------------------------------------------------------
    def _apply_run_filter(self, selected_id: str | None = None) -> None:
        """Filter ``self.all_runs`` by the active module and rebuild list."""
        if self.active_module:
            filtered = [
                r
                for r in self.all_runs
                if self.active_module in r.get("modules_w", [])
                or self.active_module in r.get("modules_b", [])
            ]
        else:
            filtered = list(self.all_runs)

        self.runs = filtered
        self.run_list.clear()
        for run in self.runs:
            result: str | None = run.get("result")
            game_id = run.get("game_id", "<unknown>")
            label = (
                f"{game_id} ({result})"
                if result and result != "*"
                else game_id
            )
            self.run_list.addItem(label)

        if not self.runs:
            self._on_run_selected(-1)
            return

        row = 0
        if selected_id:
            row = next(
                (i for i, r in enumerate(self.runs) if r.get("game_id") == selected_id),
                0,
            )
        self.run_list.setCurrentRow(row)

    # --------------------------------------------------------------
    def _refresh_runs(self) -> None:
        """Reload run files and update UI, preserving selection if possible."""
        selected_id = self.current_run.get("game_id") if self.current_run else None

        self.all_runs = load_runs("runs")
        self.overall_chart.set_data(aggregate_module_usage(self.all_runs))
        self.usage_table.set_data(read_usage())
        self._apply_run_filter(selected_id)

    # --------------------------------------------------------------
    def _on_overall_module_click(self, module: str) -> None:
        if self.active_module == module:
            self.active_module = None
        else:
            self.active_module = module
        self.overall_chart.set_selected(self.active_module)
        self._apply_run_filter()

    # --------------------------------------------------------------
    def _on_run_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.runs):
            self.current_run = None
            self.timeline.set_data([], [])
            self.moves.clear()
            self._apply_fen(chess.STARTING_FEN)
            return

        run = self.runs[row]
        self.current_run = run
        self.timeline.set_data(run.get("modules_w", []), run.get("modules_b", []))

        self.moves.clear()
        for idx, san in enumerate(run.get("moves", [])):
            self.moves.addItem(f"{idx + 1}. {san}")

        first_fen = run.get("fens", [chess.STARTING_FEN])
        self._apply_fen(first_fen[0])

    # --------------------------------------------------------------
    def _on_timeline_click(self, idx: int, is_white: bool) -> None:
        if not self.current_run:
            return
        self.timeline.set_selected(idx, is_white)
        fen_idx = idx * 2 + (0 if is_white else 1)
        fens = self.current_run.get("fens", [])
        if 0 <= fen_idx < len(fens):
            self._apply_fen(fens[fen_idx])
        if 0 <= fen_idx < self.moves.count():
            self.moves.setCurrentRow(fen_idx)

    # --------------------------------------------------------------
    def _apply_fen(self, fen: str) -> None:
        """Load *fen* into the mini board, normalising ``startpos``."""
        if fen == "startpos":
            fen = chess.STARTING_FEN
        self.board.set_fen(fen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = RunViewer()
    viewer.show()
    sys.exit(app.exec())
