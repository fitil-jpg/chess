"""Miniature chess board widget.

This widget displays a scaled-down chess board.  It is intended for
showing positions without interaction – for example, as a preview or in
dashboards.  The implementation reuses :class:`Cell` so it honours the
same overlay logic provided by :class:`DrawerManager` while rendering at a
fraction of the normal size.
"""

from __future__ import annotations

import chess
from PySide6.QtWidgets import QWidget, QFrame, QGridLayout

from ui.cell import Cell
from ui.drawer_manager import DrawerManager
from core.piece import piece_class_factory


class MiniBoard(QWidget):
    """A non-interactive, scaled board for displaying FEN positions."""

    def __init__(self, parent=None, scale: float = 0.25):
        super().__init__(parent)
        self.scale = scale
        self.board = chess.Board()
        self.drawer_manager = DrawerManager()

        board_size = int(60 * 8 * scale)
        self.board_frame = QFrame(self)
        self.board_frame.setFixedSize(board_size, board_size)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.board_frame, 0, 0)

        self.grid = QGridLayout(self.board_frame)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)

        self.cell_grid = [[None for _ in range(8)] for _ in range(8)]
        for row in range(8):
            for col in range(8):
                cell = Cell(row, col, self.drawer_manager, scale=scale)
                self.grid.addWidget(cell, row, col)
                self.cell_grid[row][col] = cell

    # ------------------------------------------------------------------
    def set_fen(self, fen: str) -> None:
        """Load a position from ``fen`` and redraw the board."""

        self.board.set_fen(fen)
        self._refresh_board()

    # ------------------------------------------------------------------
    def _refresh_board(self) -> None:
        piece_objects = {}
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                pos = (chess.square_rank(square), chess.square_file(square))
                piece_objects[square] = piece_class_factory(piece, pos)

        self.drawer_manager.collect_overlays(piece_objects, self.board)

        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                cell = self.cell_grid[row][col]
                cell.set_piece(piece.symbol() if piece else None)
                attackers = self.board.attackers(not self.board.turn, square)
                cell.set_attack_count(len(attackers))
                cell.set_highlight(False)
                cell.update()

