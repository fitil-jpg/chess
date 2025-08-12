# core/utils.py
from core.piece import Piece, Pawn, Rook, Knight, Bishop, Queen, King

def piece_class_factory(piece, pos):
    t = piece.symbol().lower()
    if t == 'p':
        return Pawn(piece.color, pos)
    elif t == 'r':
        return Rook(piece.color, pos)
    elif t == 'n':
        return Knight(piece.color, pos)
    elif t == 'b':
        return Bishop(piece.color, pos)
    elif t == 'q':
        return Queen(piece.color, pos)
    elif t == 'k':
        return King(piece.color, pos)
    return Piece(piece.color, pos)

def type_piece_name(piece):
    t = piece.symbol().lower()
    return {
        'p': 'Pawn',
        'r': 'Rook',
        'n': 'Knight',
        'b': 'Bishop',
        'q': 'Queen',
        'k': 'King'
    }.get(t, 'Piece')
