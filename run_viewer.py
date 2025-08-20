import sys
import chess
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QListWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRect

from ui.mini_board import MiniBoard
from ui.usage_timeline import UsageTimeline
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage
from utils.module_colors import MODULE_COLORS


class OverallUsageChart(QWidget):
    """Simple bar chart summarising module usage across multiple runs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counts = {}
        self.setMinimumSize(280, 150)

    def set_data(self, counts):
        self.counts = dict(counts)
        self.update()

    def paintEvent(self, ev):  # pragma: no cover - GUI drawing
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        if not self.counts:
            return

        w = self.width()
        pad = 8
        bar_h = 14
        y = pad
        max_count = max(self.counts.values())
        items = sorted(self.counts.items(), key=lambda kv: (-kv[1], kv[0]))

        for name, count in items:
            bar_w = int((w - pad * 2) * (count / max_count)) if max_count else 0
            color = MODULE_COLORS.get(name, MODULE_COLORS["OTHER"])
            painter.fillRect(QRect(pad, y, bar_w, bar_h), color)
            painter.setPen(QPen(QColor(60, 60, 60)))
            painter.drawRect(QRect(pad, y, bar_w, bar_h))
            painter.drawText(pad + bar_w + 4, y + bar_h - 2, f"{name} ({count})")
            y += bar_h + pad
            if y + bar_h > self.height():
                break


class RunViewer(QWidget):
    """Simple dashboard for inspecting recorded bot runs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Run Viewer")
        self.runs = load_runs("runs")
        self.current_run = None

        # --- Left panel: list of run files ---
        self.run_list = QListWidget()
        for run in self.runs:
            result = run.get("result")
            game_id = run.get("game_id", "<unknown>")
            label = f"{game_id} ({result})" if result else game_id
            self.run_list.addItem(label)
        self.run_list.currentRowChanged.connect(self._on_run_selected)

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
        top.addWidget(self.run_list)
        top.addLayout(centre)
        top.addLayout(right)

        # --- Bottom: overall usage chart ---
        self.overall_chart = OverallUsageChart()
        self.overall_chart.set_data(aggregate_module_usage(self.runs))

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.overall_chart)

        if self.runs:
            self.run_list.setCurrentRow(0)

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
