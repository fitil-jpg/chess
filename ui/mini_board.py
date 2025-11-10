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
from PySide6.QtCore import Qt

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
        self._border_highlights: set[int] = set()

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
                # Ensure the miniature board remains passive by ignoring
                # mouse events on each cell.
                cell.setAttribute(Qt.WA_TransparentForMouseEvents)
                self.grid.addWidget(cell, row, col)
                self.cell_grid[row][col] = cell

    # ------------------------------------------------------------------
    def set_fen(self, fen: str) -> None:
        """Load a position from ``fen`` and redraw the board."""

        self.board.set_fen(fen)
        self._refresh_board()

    # ------------------------------------------------------------------
    def set_border_highlights(self, squares) -> None:
        """Update the border highlight set using python-chess square indices."""

        new = {int(sq) for sq in squares}
        if new == self._border_highlights:
            return

        self._border_highlights = new
        self._apply_border_highlights()

    # ------------------------------------------------------------------
    def get_border_highlights(self) -> set[int]:
        """Return a copy of the active border highlight squares."""

        return set(self._border_highlights)

    # ------------------------------------------------------------------
    def request_repaint(self) -> None:
        """Request a repaint for all cells (used by :class:`core.board.ChessBoard`)."""

        for row in range(8):
            for col in range(8):
                self.cell_grid[row][col].update()

    # ------------------------------------------------------------------
    def _refresh_board(self) -> None:
        piece_objects = {}
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                pos = (chess.square_rank(square), chess.square_file(square))
                piece_objects[square] = piece_class_factory(piece, pos)

        self.drawer_manager.collect_overlays(piece_objects, self.board)
        last_move = self.board.move_stack[-1] if self.board.move_stack else None
        highlights = set()
        if last_move:
            fr = 7 - chess.square_rank(last_move.from_square)
            fc = chess.square_file(last_move.from_square)
            tr = 7 - chess.square_rank(last_move.to_square)
            tc = chess.square_file(last_move.to_square)
            highlights.add((fr, fc))
            highlights.add((tr, tc))

        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)
                cell = self.cell_grid[row][col]
                cell.set_piece(piece.symbol() if piece else None)
                attackers = self.board.attackers(not self.board.turn, square)
                cell.set_attack_count(len(attackers))
                cell.set_highlight((row, col) in highlights)
                cell.set_border_highlight(
                    square in self._border_highlights
                )
                cell.update()

    def set_board(self, board):
        """Set the chess board and refresh the display."""
        self.board = board
        self._refresh_board()

    # ------------------------------------------------------------------
    def _apply_border_highlights(self) -> None:
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                self.cell_grid[row][col].set_border_highlight(
                    square in self._border_highlights
                )

