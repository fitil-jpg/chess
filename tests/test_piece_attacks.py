import chess

from core.piece import piece_class_factory


def make_piece(board: chess.Board, square: int):
    """Wrap a python-chess piece as a project ``Piece`` instance."""
    piece = board.piece_at(square)
    pos = (chess.square_rank(square), chess.square_file(square))
    return piece_class_factory(piece, pos)


def test_rook_attacks_match_board_attacks():
    board = chess.Board()
    board.clear()
    sq = chess.D4
    board.set_piece_at(sq, chess.Piece(chess.ROOK, chess.WHITE))
    rook = make_piece(board, sq)
    assert rook.get_attacked_squares(board) == set(board.attacks(sq))


def test_knight_attacks_match_board_attacks():
    board = chess.Board()
    board.clear()
    sq = chess.E4
    board.set_piece_at(sq, chess.Piece(chess.KNIGHT, chess.WHITE))
    knight = make_piece(board, sq)
    assert knight.get_attacked_squares(board) == set(board.attacks(sq))
