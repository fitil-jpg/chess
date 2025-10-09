"""Material based evaluation with dynamic king value."""

from __future__ import annotations

import chess
from collections import OrderedDict
from typing import Tuple

import logging
logger = logging.getLogger(__name__)

from ..chess_bot import calculate_king_value

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

# Simple bounded LRU cache for evaluations keyed by (zobrist, turn)
_EVAL_CACHE_CAP = 50000
_EVAL_CACHE: "OrderedDict[Tuple[int, bool], float]" = OrderedDict()


def _cache_get(key: Tuple[int, bool]) -> float | None:
    val = _EVAL_CACHE.get(key)
    if val is not None:
        _EVAL_CACHE.move_to_end(key)
    return val


def _cache_put(key: Tuple[int, bool], value: float) -> None:
    _EVAL_CACHE[key] = value
    _EVAL_CACHE.move_to_end(key)
    if len(_EVAL_CACHE) > _EVAL_CACHE_CAP:
        _EVAL_CACHE.popitem(last=False)


def evaluate_position(board: chess.Board) -> float:
    """Evaluate ``board`` from the side to move perspective with caching."""

    # Version-tolerant position key
    def _coerce_key(value) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, (str, bytes, bytearray)):
            return hash(value)
        try:
            return hash(tuple(value))
        except TypeError:
            return hash(repr(value))

    def _position_key(b: chess.Board) -> int:
        tk = getattr(b, "transposition_key", None)
        if tk is not None:
            return _coerce_key(tk() if callable(tk) else tk)
        priv = getattr(b, "_transposition_key", None)
        if priv is not None:
            return _coerce_key(priv())
        return hash(b.fen())

    key: Tuple[int, bool] = (_position_key(board), board.turn)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    score = 0.0
    wking = calculate_king_value(board, chess.WHITE)
    bking = calculate_king_value(board, chess.BLACK)

    for _, piece in board.piece_map().items():
        val = PIECE_VALUES[piece.piece_type]
        if piece.piece_type == chess.KING:
            val = wking if piece.color == chess.WHITE else bking
        score += val if piece.color == chess.WHITE else -val

    score = score if board.turn == chess.WHITE else -score
    _cache_put(key, score)
    return score


def evaluate_positions(boards: list[chess.Board]) -> list[float]:
    """Evaluate a batch of ``boards`` with caching."""

    return [evaluate_position(b) for b in boards]

# Backwards compatibility
evaluate_board = evaluate_position
evaluate_boards = evaluate_positions
