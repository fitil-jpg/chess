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
from ui.usage_pie import UsagePie
from utils.module_usage import aggregate_module_usage


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
            result = run.get("result")
            label = f"{game_id} ({result})" if result else game_id
            self.list_widget.addItem(label)
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
        self.moves.currentRowChanged.connect(self._on_move_selected)
        right = QVBoxLayout()
        right.addWidget(self.board)
        right.addWidget(QLabel("Moves"))
        right.addWidget(self.moves)

        # --- Overall module usage pie --------------------------------------------
        self.usage_pie = UsagePie()
        self.usage_counts = aggregate_module_usage(self.runs)
        self.usage_pie.set_counts(self.usage_counts)

        # --- Assemble layout ------------------------------------------------------
        layout_main = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(self.list_widget)
        top.addLayout(centre)
        top.addLayout(right)
        layout_main.addLayout(top)
        pie_box = QVBoxLayout()
        pie_box.addWidget(QLabel("Overall module usage"))
        pie_box.addWidget(self.usage_pie)
        layout_main.addLayout(pie_box)

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
    def _on_move_selected(self, row: int) -> None:
        """Show the position for the move selected in the list."""
        if not self.current_run or row < 0:
            return

        idx = row // 2
        is_white = (row % 2) == 0
        self._on_timeline_click(idx, is_white)

    # ------------------------------------------------------------------
    def _on_timeline_click(self, idx: int, is_white: bool) -> None:
        """Show the position for the clicked move and highlight it.

        ``idx`` is the 0-based ply index within the selected run while
        ``is_white`` indicates whether the move belongs to White.  The method
        updates the mini board to the corresponding FEN and selects the move in
        the textual list, if available.
        """

        if not self.current_run:
            return

        # ``fens`` contains the starting position followed by a FEN after
        # every played move.  ``idx`` therefore refers to the ply number for
        # the colour indicated by ``is_white``.  Convert this to the index of
        # the resulting board position and highlight the corresponding move in
        # the textual list.
        fen_idx = idx * 2 + (1 if is_white else 2)
        fens = self.current_run.get("fens", [])
        if 0 <= fen_idx < len(fens):
            self._apply_fen(fens[fen_idx])

        move_row = fen_idx - 1
        if 0 <= move_row < self.moves.count():
            self.moves.setCurrentRow(move_row)

    # ------------------------------------------------------------------
    def _apply_fen(self, fen: str) -> None:
        """Load *fen* into the mini board, normalising ``startpos``."""
        if fen == "startpos":
            fen = chess.STARTING_FEN
        self.board.set_fen(fen)
