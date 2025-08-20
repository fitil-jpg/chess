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

from ui.mini_board import MiniBoard
from ui.usage_timeline import UsageTimeline
from ui.usage_pie import UsagePie
from utils.load_runs import load_runs
from utils.module_usage import aggregate_module_usage


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

        # --- Bottom: overall usage pie ---
        self.usage_pie = UsagePie()
        self.usage_pie.set_counts(aggregate_module_usage(self.runs))

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(QLabel("Overall module usage"))
        layout.addWidget(self.usage_pie)

        if self.runs:
            self.run_list.setCurrentRow(0)

    # --------------------------------------------------------------
    def _refresh_runs(self) -> None:
        """Reload run files and update UI, preserving selection if possible."""
        selected_id = self.current_run.get("game_id") if self.current_run else None

        self.runs = load_runs("runs")

        self.run_list.clear()
        for run in self.runs:
            result = run.get("result")
            game_id = run.get("game_id", "<unknown>")
            label = f"{game_id} ({result})" if result else game_id
            self.run_list.addItem(label)

        self.usage_pie.set_counts(aggregate_module_usage(self.runs))

        if not self.runs:
            self._on_run_selected(-1)
            return

        row = next((i for i, r in enumerate(self.runs) if r.get("game_id") == selected_id), 0)
        self.run_list.setCurrentRow(row)

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
