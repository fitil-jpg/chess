import chess
import pytest

from core.piece import piece_class_factory


def test_rook_attacks_and_defense():
    board = chess.Board()
    board.clear()
    rook_sq = chess.square(3, 3)  # d4
    board.set_piece_at(rook_sq, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.square(3, 5), chess.Piece(chess.PAWN, chess.WHITE))  # d6
    board.set_piece_at(chess.square(6, 3), chess.Piece(chess.PAWN, chess.BLACK))  # g4

    pos = (chess.square_rank(rook_sq), chess.square_file(rook_sq))
    rook = piece_class_factory(board.piece_at(rook_sq), pos)

    expected_attacks = set(board.attacks(rook_sq))
    assert rook.get_attacked_squares(board) == expected_attacks

    rook.update_defended(board)
    assert rook.defended_moves == {chess.square(3, 5)}
    assert rook.attacked_moves == expected_attacks - {chess.square(3, 5)}


def test_knight_attacks():
    board = chess.Board()
    board.clear()
    knight_sq = chess.square(4, 3)  # e4
    board.set_piece_at(knight_sq, chess.Piece(chess.KNIGHT, chess.WHITE))

    pos = (chess.square_rank(knight_sq), chess.square_file(knight_sq))
    knight = piece_class_factory(board.piece_at(knight_sq), pos)

    expected_attacks = set(board.attacks(knight_sq))
    assert knight.get_attacked_squares(board) == expected_attacks


@pytest.mark.parametrize(
    "piece_type, square",
    [
        (chess.BISHOP, chess.square(2, 2)),  # c3
        (chess.QUEEN, chess.square(4, 4)),  # e5
        (chess.KING, chess.square(4, 4)),  # e5
        (chess.PAWN, chess.square(3, 3)),  # d4
    ],
)
def test_other_pieces_attacks(piece_type, square):
    board = chess.Board()
    board.clear()
    board.set_piece_at(square, chess.Piece(piece_type, chess.WHITE))

    pos = (chess.square_rank(square), chess.square_file(square))
    piece = piece_class_factory(board.piece_at(square), pos)

    expected_attacks = set(board.attacks(square))
    assert piece.get_attacked_squares(board) == expected_attacks
