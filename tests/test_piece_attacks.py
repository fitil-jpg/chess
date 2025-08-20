import chess

from core.piece import piece_class_factory


def _piece_from_square(board: chess.Board, square: int):
    piece = board.piece_at(square)
    assert piece is not None
    pos = (chess.square_rank(square), chess.square_file(square))
    return piece_class_factory(piece, pos)


def test_rook_attacks_match_python_chess():
    board = chess.Board("8/8/8/3R4/8/8/8/8 w - - 0 1")
    rook = _piece_from_square(board, chess.D5)
    assert rook.get_attacked_squares(board) == board.attacks(chess.D5)


def test_knight_attacks_match_python_chess():
    board = chess.Board("8/8/8/3N4/8/8/8/8 w - - 0 1")
    knight = _piece_from_square(board, chess.D5)
    assert knight.get_attacked_squares(board) == board.attacks(chess.D5)
