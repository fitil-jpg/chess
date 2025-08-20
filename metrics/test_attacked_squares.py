import chess
from attacked_squares import calculate_attacked_squares


def test_attacked_squares():
    # Set up a simple position
    board = chess.Board()
    board.set_fen("8/8/8/8/8/8/8/R7 w - - 0 1")
    square = chess.E1
    board.set_piece_at(square, chess.Piece(chess.ROOK, chess.WHITE))

    result = calculate_attacked_squares(square, board)

    # Check the number of attacked squares
    expected_number_of_squares = 14  # Rook on e1 with another rook on a1
    assert len(result) == expected_number_of_squares, \
        f"Expected {expected_number_of_squares}, but got {len(result)}."

    print("test_attacked_squares passed!")


if __name__ == "__main__":
    test_attacked_squares()
