import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vendors"))
)

import chess
import pytest
from attacked_squares import calculate_attacked_squares


def test_attacked_squares() -> None:
    """Verify the number of squares a rook attacks."""
    board = chess.Board()
    board.clear()
    square = chess.E1
    piece = chess.Piece(chess.ROOK, chess.WHITE)
    board.set_piece_at(square, piece)

    result = calculate_attacked_squares(square, board)
    expected = list(board.attacks(square))

    assert result == expected
    assert len(result) == 14  # Rook on e1 on an otherwise empty board


def test_missing_piece() -> None:
    """Ensure a ``ValueError`` is raised when the piece is absent."""
    board = chess.Board()
    board.clear()
    square = chess.A1

    with pytest.raises(ValueError):
        calculate_attacked_squares(square, board)
