import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vendors"))
)

import chess
from attacked_squares import calculate_attacked_squares


def test_attacked_squares() -> None:
    """Verify the number of squares a rook attacks."""
    board = chess.Board()
    board.set_fen("8/8/8/8/8/8/8/R7 w - - 0 1")
    square = chess.E1
    board.set_piece_at(square, chess.Piece(chess.ROOK, chess.WHITE))

    result = calculate_attacked_squares(square, board)
    expected = list(board.attacks(square))

    assert result == expected
    assert len(result) == 14  # Rook on e1 with another rook on a1
