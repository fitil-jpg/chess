"""A tiny subset of the python-chess API used for unit tests.

This lightweight module implements only the features required by the
metrics unit tests.  It is **not** a complete chess engine.
"""

from __future__ import annotations

# piece colours
WHITE = True
BLACK = False
Color = bool  # type alias for annotations

# piece types
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = range(1, 7)

FILES = "abcdefgh"
RANKS = "12345678"


def square_file(sq: int) -> int:
    return sq % 8


def square_rank(sq: int) -> int:
    return sq // 8


class SquareSet(set):
    """Simple set subclass used to mirror python-chess API."""

    def __init__(self, iterable=None):
        super().__init__(iterable or [])


# generate square constants like A1, B1 ... H8
for r in range(8):
    for f in range(8):
        name = FILES[f].upper() + RANKS[r]
        globals()[name] = r * 8 + f


class Piece:
    def __init__(self, piece_type: int, color: bool):
        self.piece_type = piece_type
        self.color = color


# pre-compute king attacks
_DEF_KING_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1),
]


def _king_attacks(sq: int):
    f, r = square_file(sq), square_rank(sq)
    moves = []
    for df, dr in _DEF_KING_OFFSETS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            moves.append(nr * 8 + nf)
    return moves


KING_ATTACKS = {sq: SquareSet(_king_attacks(sq)) for sq in range(64)}


class Board:
    def __init__(self):
        self._pieces: dict[int, Piece] = {}

    @classmethod
    def empty(cls) -> "Board":
        return cls()

    def set_piece_at(self, square: int, piece: Piece) -> None:
        self._pieces[square] = piece

    def piece_at(self, square: int) -> Piece | None:
        return self._pieces.get(square)

    def piece_map(self) -> dict[int, Piece]:
        return dict(self._pieces)

    def pieces(self, piece_type: int, color: bool) -> set[int]:
        return {sq for sq, p in self._pieces.items() if p.piece_type == piece_type and p.color == color}

    def king(self, color: bool) -> int | None:
        for sq, p in self._pieces.items():
            if p.piece_type == KING and p.color == color:
                return sq
        return None

    # --- attack calculations ----------------------------------------------
    def attacks(self, square: int) -> SquareSet:
        piece = self.piece_at(square)
        if not piece:
            return SquareSet()
        if piece.piece_type == PAWN:
            return SquareSet(self._pawn_attacks(square, piece.color))
        if piece.piece_type == KNIGHT:
            return SquareSet(self._knight_moves(square))
        if piece.piece_type == KING:
            return SquareSet(KING_ATTACKS[square])
        return SquareSet(self._sliding_attacks(square, piece))

    def is_attacked_by(self, color: bool, square: int) -> bool:
        for sq, p in self._pieces.items():
            if p.color == color:
                if square in self.attacks(sq):
                    return True
        return False

    # helper functions ----------------------------------------------------
    def _knight_moves(self, square: int):
        offsets = [
            (1, 2), (2, 1), (-1, 2), (-2, 1),
            (1, -2), (2, -1), (-1, -2), (-2, -1),
        ]
        f, r = square_file(square), square_rank(square)
        moves = []
        for df, dr in offsets:
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                moves.append(nr * 8 + nf)
        return moves

    def _pawn_attacks(self, square: int, color: bool):
        f, r = square_file(square), square_rank(square)
        direction = 1 if color == WHITE else -1
        moves = []
        for df in (-1, 1):
            nf, nr = f + df, r + direction
            if 0 <= nf < 8 and 0 <= nr < 8:
                moves.append(nr * 8 + nf)
        return moves

    def _sliding_attacks(self, square: int, piece: Piece):
        directions = []
        if piece.piece_type in (ROOK, QUEEN):
            directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if piece.piece_type in (BISHOP, QUEEN):
            directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        f, r = square_file(square), square_rank(square)
        moves = []
        for df, dr in directions:
            nf, nr = f + df, r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                nsq = nr * 8 + nf
                moves.append(nsq)
                if nsq in self._pieces:
                    break
                nf += df
                nr += dr
        return moves


__all__ = [
    "WHITE",
    "BLACK",
    "PAWN",
    "KNIGHT",
    "BISHOP",
    "ROOK",
    "QUEEN",
    "KING",
    "Piece",
    "Board",
    "SquareSet",
    "square_file",
    "square_rank",
    "Color",
] + [FILES[f].upper() + RANKS[r] for r in range(8) for f in range(8)]
