import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vendors"))

import chess
from attacked_squares import calculate_attacked_squares


def test_attacked_squares():
    # Set up a simple position
    board = chess.Board()
    board.set_fen("8/8/8/8/8/8/8/R7 w - - 0 1")
    board.set_piece_at(chess.E1, chess.Piece(chess.ROOK, chess.WHITE))

    result = calculate_attacked_squares(board, chess.E1)

    # Check the number of attacked squares
    expected_number_of_squares = 14  # Rook on e1 with another rook on a1
    assert len(result) == expected_number_of_squares, (
        f'Expected {expected_number_of_squares}, but got {len(result)}.'
    )


if __name__ == "__main__":
    test_attacked_squares()
