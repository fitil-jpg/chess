import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")
pytest.importorskip("chess")

import chess as chess_mod
from PySide6.QtWidgets import QApplication

from core.board import ChessBoard
from ui.mini_board import MiniBoard


class RecordingMiniBoard(MiniBoard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repaint_calls = 0

    def request_repaint(self) -> None:  # type: ignore[override]
        self.repaint_calls += 1
        super().request_repaint()


def test_highlight_hooks_update_miniboard():
    app = QApplication.instance() or QApplication([])
    view = RecordingMiniBoard(scale=0.3)
    board = ChessBoard(view=view)

    knight_fen = "8/8/8/3N4/8/8/8/8 w - - 0 1"
    board.load_fen(knight_fen)
    view.set_fen(knight_fen)

    highlighted = board.select_square(chess_mod.D5)

    assert set(highlighted) == view.get_border_highlights()
    assert view.repaint_calls >= 1

    board.clear_selection()
    assert view.get_border_highlights() == set()
    assert view.repaint_calls >= 2

    view.deleteLater()
    if QApplication.instance() is not None:
        QApplication.processEvents()
