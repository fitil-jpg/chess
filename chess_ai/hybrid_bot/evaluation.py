"""Simple evaluation with dynamic king coefficient."""

from __future__ import annotations

import chess

# Basic piece values in centipawns
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


def dynamic_king_coeff(board: chess.Board) -> float:
    """Return a coefficient [1,2] that grows as pieces leave the board."""
    total = len(board.piece_map())
    phase = total / 32.0
    # Early game -> coeff≈1, endgame -> coeff≈2
    return 1.0 + (1.0 - phase)


def _king_activity(board: chess.Board, color: bool) -> float:
    """Simple king activity metric: closer to centre is better."""
    sq = board.king(color)
    if sq is None:
        return 0.0
    rank = chess.square_rank(sq)
    file = chess.square_file(sq)
    # Manhattan distance from board centre (3.5,3.5)
    dist = abs(3.5 - rank) + abs(3.5 - file)
    return -dist


def evaluate_board(board: chess.Board) -> float:
    """Evaluate ``board`` from the side to move perspective."""
    score = 0.0
    coeff = dynamic_king_coeff(board)
    for sq, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type]
        if piece.piece_type == chess.KING:
            val += coeff * _king_activity(board, piece.color)
        score += val if piece.color == chess.WHITE else -val
    # Convert to side to move perspective
    return score if board.turn == chess.WHITE else -score

