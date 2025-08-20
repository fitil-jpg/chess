"""Utility helpers and shared data structures for the core package."""

from dataclasses import dataclass

from core.piece import Piece, Pawn, Rook, Knight, Bishop, Queen, King


@dataclass
class GameContext:
    """Shared positional metrics available to all agents."""

    material_diff: int = 0
    mobility: int = 0
    king_safety: int = 0

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
