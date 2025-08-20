import chess
import pytest
from metrics.attacked_squares import calculate_attacked_squares


def test_attacked_squares() -> None:
    """Verify the number of squares a rook attacks."""
    board = chess.Board()
    board.clear()
    square = chess.E1
    piece = chess.Piece(chess.ROOK, chess.WHITE)
    board.set_piece_at(square, piece)

    result = calculate_attacked_squares(piece, board)
    expected = list(board.attacks(square))

    assert result == expected
    assert len(result) == 14  # Rook on e1 on an otherwise empty board


def test_calculate_attacked_squares_missing_piece_raises_value_error() -> None:
    """``calculate_attacked_squares`` raises ``ValueError`` if the piece is absent."""
    board = chess.Board()
    board.clear()
    missing_piece = chess.Piece(chess.BISHOP, chess.WHITE)

    with pytest.raises(ValueError):
        calculate_attacked_squares(missing_piece, board)

