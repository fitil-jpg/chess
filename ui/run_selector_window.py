from __future__ import annotations

import chess
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
)

from ui.mini_board import MiniBoard
from ui.usage_timeline import UsageTimeline


class RunSelectorWindow(QWidget):
    """Window that displays available recorded runs."""

    def __init__(self, runs):
        super().__init__()
        self.setWindowTitle("Run Selector")
        self.runs = list(runs)
        self.current_run = None

        # --- Left panel: run list -------------------------------------------------
        self.list_widget = QListWidget()
        for run in self.runs:
            game_id = run.get("game_id", "<unknown>")
            self.list_widget.addItem(game_id)
        self.list_widget.currentRowChanged.connect(self._on_run_selected)

        # --- Centre: usage timeline ----------------------------------------------
        self.timeline = UsageTimeline()
        self.timeline.moveClicked.connect(self._on_timeline_click)
        centre = QVBoxLayout()
        centre.addWidget(QLabel("Usage timeline"))
        centre.addWidget(self.timeline)

        # --- Right: board and moves list -----------------------------------------
        self.board = MiniBoard(scale=0.5)
        self.moves = QListWidget()
        right = QVBoxLayout()
        right.addWidget(self.board)
        right.addWidget(QLabel("Moves"))
        right.addWidget(self.moves)

        # --- Assemble layout ------------------------------------------------------
        layout = QHBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addLayout(centre)
        layout.addLayout(right)

        if self.runs:
            self.list_widget.setCurrentRow(0)

    # ------------------------------------------------------------------
    def _on_run_selected(self, row: int) -> None:
        """Load run at *row* and refresh widgets."""
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

    # ------------------------------------------------------------------
    def _on_timeline_click(self, idx: int, is_white: bool) -> None:
        if not self.current_run:
            return
        fen_idx = idx * 2 + (0 if is_white else 1)
        fens = self.current_run.get("fens", [])
        if 0 <= fen_idx < len(fens):
            self._apply_fen(fens[fen_idx])
        if 0 <= fen_idx < self.moves.count():
            self.moves.setCurrentRow(fen_idx)

    # ------------------------------------------------------------------
    def _apply_fen(self, fen: str) -> None:
        """Load *fen* into the mini board, normalising ``startpos``."""
        if fen == "startpos":
            fen = chess.STARTING_FEN
        self.board.set_fen(fen)
