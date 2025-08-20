import chess
import pytest

from attacked_squares import calculate_attacked_squares


def test_attacked_squares_returns_attacks():
    board = chess.Board()
    board.clear()
    square = chess.E1
    piece = chess.Piece(chess.ROOK, chess.WHITE)
    board.set_piece_at(square, piece)

    result = calculate_attacked_squares(piece, board)
    expected = list(board.attacks(square))
    assert result == expected


def test_missing_piece_raises_value_error():
    board = chess.Board()
    board.clear()
    piece = chess.Piece(chess.BISHOP, chess.WHITE)

    with pytest.raises(ValueError):
        calculate_attacked_squares(piece, board)
