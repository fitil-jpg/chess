import chess

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
