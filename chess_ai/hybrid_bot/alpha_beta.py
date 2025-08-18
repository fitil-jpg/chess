"""Alpha-beta search with several common enhancements."""

from __future__ import annotations

import math
import chess
from .evaluation import evaluate_board


INF = 10 ** 9


def quiescence(board: chess.Board, alpha: float, beta: float) -> float:
    """Capture-only search to resolve tactical instability."""
    stand = evaluate_board(board)
    if stand >= beta:
        return beta
    if alpha < stand:
        alpha = stand
    for move in board.legal_moves:
        if not board.is_capture(move):
            continue
        board.push(move)
        score = -quiescence(board, -beta, -alpha)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def _pvs(board: chess.Board, depth: int, alpha: float, beta: float, allow_null: bool = True) -> float:
    if depth == 0 or board.is_game_over():
        return quiescence(board, alpha, beta)

    if allow_null and depth >= 2 and not board.checkers():
        board.push(chess.Move.null())
        score = -_pvs(board, depth - 1 - 2, -beta, -beta + 1, False)
        board.pop()
        if score >= beta:
            return beta

    best_val = -INF
    first = True
    for idx, move in enumerate(board.legal_moves):
        board.push(move)
        if first:
            val = -_pvs(board, depth - 1, -beta, -alpha, True)
            first = False
        else:
            # Late move reduction for quieter moves
            reduce = 1 if idx >= 3 and depth >= 3 and not board.is_capture(move) else 0
            val = -_pvs(board, depth - 1 - reduce, -alpha - 1, -alpha, True)
            if alpha < val < beta:
                val = -_pvs(board, depth - 1, -beta, -val, True)
        board.pop()
        if val > best_val:
            best_val = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best_val


def search(board: chess.Board, depth: int) -> tuple[float, chess.Move | None]:
    best_move = None
    alpha, beta = -INF, INF
    best_val = -INF
    for move in board.legal_moves:
        board.push(move)
        val = -_pvs(board, depth - 1, -beta, -alpha, True)
        board.pop()
        if val > best_val:
            best_val, best_move = val, move
        if val > alpha:
            alpha = val
    return best_val, best_move

