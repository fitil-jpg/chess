import chess
import pytest
from metrics.attacked_squares import calculate_attacked_squares


def test_attacked_squares() -> None:
    """Verify the number of squares a rook attacks."""
    board = chess.Board("8/8/8/8/8/8/8/4R3 w - - 0 1")
    square = chess.E1

    result = calculate_attacked_squares(board, square)
    expected = list(board.attacks(square))

    assert result == expected
    assert len(result) == 14  # Rook on e1 on an otherwise empty board  


def test_calculate_attacked_squares_missing_piece_raises_value_error() -> None:
    """``calculate_attacked_squares`` raises ``ValueError`` if the square is empty."""
    board = chess.Board()
    board.clear()
    square = chess.E1

    with pytest.raises(ValueError):
        calculate_attacked_squares(board, square)


def test_calculate_attacked_squares_empty_e2_raises_value_error() -> None:
    """``calculate_attacked_squares`` raises ``ValueError`` if E2 is empty."""
    board = chess.Board()
    board.clear()

    with pytest.raises(ValueError):
        calculate_attacked_squares(board, chess.E2)
