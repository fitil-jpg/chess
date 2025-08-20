"""Material based evaluation with dynamic king value."""

from __future__ import annotations

import chess

from ..piece_values import dynamic_piece_value

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

    The king's value is defined as the sum of its allied pieces' dynamic
    values.  If the opponent has lost major material (e.g. the queen), the
    king becomes relatively safer and its value increases slightly.
    """

    if color is None:
        color = board.turn

    value = 0
    for _, piece in board.piece_map().items():
        if piece.color == color and piece.piece_type != chess.KING:
            value += dynamic_piece_value(piece, board)

    if not board.pieces(chess.QUEEN, not color):
        value = int(value * 1.1)

    return value


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


def evaluate_positions(boards: list[chess.Board]) -> list[float]:
    """Evaluate a batch of ``boards`` in one call.

    This helper simply applies :func:`evaluate_position` to each board in the
    provided list.  It mirrors the interface of a neural network's
    ``predict_many`` method which returns a list of values for a list of
    positions.
    """

    return [evaluate_position(b) for b in boards]


# Backwards compatibility
evaluate_board = evaluate_position
evaluate_boards = evaluate_positions

