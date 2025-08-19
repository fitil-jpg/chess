"""Material based evaluation with dynamic king value."""

from __future__ import annotations

import chess

# Basic piece values in centipawns.  The king's base value is determined
# dynamically at evaluation time.
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def calculate_king_value(board: chess.Board, color: chess.Color | None = None) -> int:
    """Return a material based value for the king.

    The value is the weighted sum of the side's remaining material using the
    formula ``p*8 + b*2 + n*2 + r*2 + q`` where ``p`` is the number of pawns,
    ``b`` bishops, ``n`` knights, ``r`` rooks and ``q`` queens.  If the
    opponent has no queen a small bonus is added as the king becomes slightly
    safer.  The returned value is expressed in centipawns.
    """

    if color is None:
        color = board.turn

    p = len(board.pieces(chess.PAWN, color))
    b = len(board.pieces(chess.BISHOP, color))
    n = len(board.pieces(chess.KNIGHT, color))
    r = len(board.pieces(chess.ROOK, color))
    q = len(board.pieces(chess.QUEEN, color))

    value = p * 8 + b * 2 + n * 2 + r * 2 + q

    # Slightly increase the value of the king when the opponent lacks a queen.
    if not board.pieces(chess.QUEEN, not color):
        value += 5

    return value * 100


def evaluate_position(board: chess.Board) -> float:
    """Evaluate ``board`` from the side to move perspective."""

    score = 0.0
    wking = calculate_king_value(board, chess.WHITE)
    bking = calculate_king_value(board, chess.BLACK)

    for _, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type]
        if piece.piece_type == chess.KING:
            val = wking if piece.color == chess.WHITE else bking
        score += val if piece.color == chess.WHITE else -val

    return score if board.turn == chess.WHITE else -score


# Backwards compatibility
evaluate_board = evaluate_position

