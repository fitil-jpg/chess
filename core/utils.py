"""Utility helpers and shared data structures for the core package."""

import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass

from core.piece import Piece, Pawn, Rook, Knight, Bishop, Queen, King


# Mapping of python-chess piece symbols to project piece classes
PIECE_CLASS_MAP = {
    'p': Pawn,
    'r': Rook,
    'n': Knight,
    'b': Bishop,
    'q': Queen,
    'k': King,
}


@dataclass
class GameContext:
    """Shared positional metrics available to all agents."""

    material_diff: int = 0
    mobility: int = 0
    king_safety: int = 0

def piece_class_factory(piece, pos):
    t = piece.symbol().lower()
    cls = PIECE_CLASS_MAP.get(t, Piece)
    return cls(piece.color, pos)

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