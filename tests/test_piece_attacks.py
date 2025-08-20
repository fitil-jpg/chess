import chess

import core.piece as piece

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


def test_get_attacked_squares_uses_prebuilt_board(monkeypatch):
    board = chess.Board()
    board.clear()
    sq = chess.D4
    board.set_piece_at(sq, chess.Piece(chess.ROOK, chess.WHITE))
    rook = make_piece(board, sq)

    calls = {'n': 0}
    original = piece.build_chess_board

    def wrapper(b):
        calls['n'] += 1
        return original(b)

    monkeypatch.setattr(piece, 'build_chess_board', wrapper)
    attacked = rook.get_attacked_squares(chess_board=board)
    assert attacked == set(board.attacks(sq))
    assert calls['n'] == 0


def test_get_defended_squares_uses_prebuilt_board(monkeypatch):
    base = chess.Board("k7/8/3P4/8/3R4/8/8/K7 w - - 0 1")
    rook = make_piece(base, chess.D4)

    calls = {'n': 0}
    original = piece.build_chess_board

    def wrapper(b):
        calls['n'] += 1
        return original(b)

    monkeypatch.setattr(piece, 'build_chess_board', wrapper)
    defended = rook.get_defended_squares(chess_board=base)
    assert defended == {chess.D6}
    assert calls['n'] == 0
