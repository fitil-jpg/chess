from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import chess


# Basic material evaluation reused by quiescence search.
# Evaluates from side to move perspective (positive is good for side to move).
_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

def _evaluate(board: chess.Board) -> int:
    """Return a simple material evaluation of ``board``.

    The function mirrors :meth:`DecisionEngine._evaluate` so that the
    quiescence search produces compatible scores with the regular search.
    The score is from the point of view of the side to move.
    """
    score = 0
    turn = board.turn
    for piece, val in _values.items():
        score += len(board.pieces(piece, turn)) * val
        score -= len(board.pieces(piece, not turn)) * val
    return score


def quiescence(board: chess.Board, alpha: int, beta: int) -> int:
    """Perform a quiescence search on ``board``.

    Parameters
    ----------
    board:
        The current board state.
    alpha, beta:
        Alpha--beta window.

    The search only explores capture and checking moves and keeps
    recursing until a quiet position is reached.  The evaluation is a
    simple material count from the point of view of the side to move.
    """
    stand_pat = _evaluate(board)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    for move in board.legal_moves:
        if not (board.is_capture(move) or board.gives_check(move)):
            continue
        board.push(move)
        score = -quiescence(board, -beta, -alpha)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha