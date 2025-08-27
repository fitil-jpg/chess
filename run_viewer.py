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
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRect, Signal

from ui.mini_board import MiniBoard
from ui.usage_timeline import UsageTimeline
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage
from utils.module_colors import MODULE_COLORS


class OverallUsageChart(QWidget):
    """Simple bar chart summarising module usage across multiple runs."""

    moduleClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counts = {}
        self._bar_rects = []  # regions for click detection
        self._selected = None
        self.setMinimumSize(280, 150)

    def set_data(self, counts):
        self.counts = dict(counts)
        self.update()

    def set_selected(self, name: str | None) -> None:
        """Highlight *name* in the chart (or clear with ``None``)."""
        self._selected = name
        self.update()

    def paintEvent(self, ev):  # pragma: no cover - GUI drawing
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        self._bar_rects = []
        if not self.counts:
            return

        w = self.width()
        pad = 8
        bar_h = 14
        legend_h = 20

        # Reserve space at the bottom for the legend so bars don't overlap it
        y = pad
        max_bar_height = self.height() - legend_h - pad
        max_count = max(self.counts.values())
        items = sorted(self.counts.items(), key=lambda kv: (-kv[1], kv[0]))

        for name, count in items:
            if y + bar_h > max_bar_height:
                break
            bar_w = int((w - pad * 2) * (count / max_count)) if max_count else 0
            rect = QRect(pad, y, bar_w, bar_h)
            self._bar_rects.append((rect, name))
            color = MODULE_COLORS.get(name, MODULE_COLORS["OTHER"])
            if self._selected and name != self._selected:
                color = color.lighter(160)
            painter.fillRect(rect, color)
            pen_width = 2 if name == self._selected else 1
            painter.setPen(QPen(QColor(60, 60, 60), pen_width))
            painter.drawRect(rect)
            painter.drawText(pad + bar_w + 4, y + bar_h - 2, f"{name} ({count})")
            y += bar_h + pad

        # Draw legend mapping colours to modules
        y_leg = self.height() - legend_h + 4
        x_leg = pad
        painter.setPen(QPen(QColor(80, 80, 80)))
        for name, _ in items:
            color = MODULE_COLORS.get(name, MODULE_COLORS["OTHER"])
            if self._selected and name != self._selected:
                color = color.lighter(160)
            rect = QRect(x_leg, y_leg, 10, 10)
            painter.fillRect(rect, color)
            painter.drawRect(rect)
            painter.drawText(x_leg + 14, y_leg + 10, name)
            x_leg += 14 + painter.fontMetrics().horizontalAdvance(name) + 10
            if x_leg > w - pad:
                break

    def mousePressEvent(self, ev):  # pragma: no cover - GUI interaction
        pos = ev.position().toPoint()
        for rect, name in self._bar_rects:
            if rect.contains(pos):
                self.moduleClicked.emit(name)
                break


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

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.overall_chart)

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
