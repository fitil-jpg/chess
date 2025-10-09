"""Advanced alpha-beta search with common enhancements.

This module implements a reasonably strong alpha-beta search routine used by
the hybrid bot.  The search incorporates a number of well known techniques
including Principal Variation Search (PVS), late move reductions (LMR),
null-move pruning, fail-soft behaviour, a transposition table, a simple
quiescence search and various move ordering heuristics (hash move, MVV-LVA,
killer moves and history heuristics).

Two hooks – :func:`generate_moves` and :func:`order_moves` – are provided so
that experiments with move generation or ordering can be easily plugged in.

The main entry point is :func:`search` which returns the best score and move
for the current side to move.  A small helper :func:`search_one_shot` is also
provided which wraps the search in a ``cProfile`` profiler for convenient
performance inspection.
"""

from __future__ import annotations

from dataclasses import dataclass
import cProfile
import logging
logger = logging.getLogger(__name__)

import io
import pstats
import time
from typing import Dict, Iterable, List, Optional, Tuple

import chess

from .evaluation import evaluate_position
from ..utils.profile_stats import STATS, plot_profile_stats


INF = 10 ** 9


# ---------------------------------------------------------------------------
#  Move generation / ordering hooks
# ---------------------------------------------------------------------------


def generate_moves(board: chess.Board) -> List[chess.Move]:
    """Return a list of legal moves for ``board``.

    This function is intentionally tiny and exists mainly as a hook that can
    be monkey patched from the outside if specialised move generation is
    desired.
    """

    return list(board.legal_moves)


# Piece values for MVV-LVA ordering.  Expressed in centipawns.
MVV_LVA_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}


def order_moves(
    board: chess.Board,
    moves: Iterable[chess.Move],
    killers: Dict[int, List[chess.Move]],
    history: Dict[Tuple[int, int, int], int],
    depth: int,
    hash_move: Optional[chess.Move],
) -> List[chess.Move]:
    """Order ``moves`` using a collection of heuristics.

    The following scheme is used (from highest to lowest priority):

    * hash move from the transposition table
    * MVV-LVA for captures
    * killer moves stored for this ply
    * history heuristic
    """

    def score(move: chess.Move) -> int:
        if hash_move is not None and move == hash_move:
            return 1_000_000
        if board.is_capture(move):
            victim = board.piece_type_at(move.to_square)
            attacker = board.piece_type_at(move.from_square)
            v_val = MVV_LVA_VALUES.get(victim, 0)
            a_val = MVV_LVA_VALUES.get(attacker, 0)
            return 100_000 + v_val * 10 - a_val
        if move in killers.get(depth, []):
            return 90_000
        return history.get((board.turn, move.from_square, move.to_square), 0)

    return sorted(moves, key=score, reverse=True)


# ---------------------------------------------------------------------------
#  Quiescence Search
# ---------------------------------------------------------------------------


def quiescence(board: chess.Board, alpha: float, beta: float, deadline: float | None = None) -> float:
    """Capture-only search to avoid the horizon effect."""

    if deadline is not None and time.monotonic() >= deadline:
        return evaluate_position(board)

    stand_pat = evaluate_position(board)
    if stand_pat >= beta:
        return stand_pat  # fail-soft: return the actual score
    if alpha < stand_pat:
        alpha = stand_pat

    for move in generate_moves(board):
        if not board.is_capture(move):
            continue
        board.push(move)
        score = -quiescence(board, -beta, -alpha, deadline)
        board.pop()
        if score >= beta:
            return score
        if score > alpha:
            alpha = score
    return alpha


# ---------------------------------------------------------------------------
#  Transposition table support
# ---------------------------------------------------------------------------

EXACT, LOWERBOUND, UPPERBOUND = 0, 1, 2


@dataclass
class TTEntry:
    depth: int
    flag: int
    value: float
    move: Optional[chess.Move]


TT: Dict[int, TTEntry] = {}


# ---------------------------------------------------------------------------
#  Alpha-beta search
# ---------------------------------------------------------------------------


def ab_search(
    board: chess.Board,
    depth: int,
    alpha: float,
    beta: float,
    allow_null: bool = True,
    ply: int = 0,
    deadline: float | None = None,
) -> Tuple[float, Optional[chess.Move]]:
    """Negamax alpha-beta search with numerous enhancements."""

    # Start profiling at the root if not already active
    if ply == 0 and STATS.start_time == 0.0:
        STATS.start()
    STATS.nodes += 1

    if deadline is not None and time.monotonic() >= deadline:
        return evaluate_position(board), None

    alpha_orig = alpha

    # Transposition table lookup (compatible across python-chess versions)
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

    key = _position_key(board)
    tt_move: Optional[chess.Move] = None
    entry = TT.get(key)
    if entry and entry.depth >= depth:
        tt_move = entry.move
        STATS.tt_hits += 1
        if entry.flag == EXACT:
            return entry.value, tt_move
        if entry.flag == LOWERBOUND and entry.value > alpha:
            alpha = entry.value
        elif entry.flag == UPPERBOUND and entry.value < beta:
            beta = entry.value
        if alpha >= beta:
            return entry.value, tt_move

    if depth == 0 or board.is_game_over():
        return quiescence(board, alpha, beta, deadline), None

    # Null move pruning
    if allow_null and depth >= 3 and not board.checkers():
        board.push(chess.Move.null())
        score, _ = ab_search(board, depth - 1 - 2, -beta, -beta + 1, False, ply + 1, deadline)
        score = -score
        board.pop()
        if score >= beta:
            return score, None

    best_val = -INF
    best_move: Optional[chess.Move] = None

    moves = generate_moves(board)
    moves = order_moves(board, moves, KILLERS, HISTORY, ply, tt_move)

    first = True
    for idx, move in enumerate(moves):
        if deadline is not None and time.monotonic() >= deadline:
            break
        board.push(move)

        # Late move reductions for quiet moves
        reduce = 0
        if idx >= 3 and depth >= 3 and not board.is_capture(move) and not board.gives_check(move):
            reduce = 1
            STATS.lmr_reductions += 1

        if first:
            score, _ = ab_search(board, depth - 1, -beta, -alpha, True, ply + 1, deadline)
            score = -score
            first = False
        else:
            score, _ = ab_search(board, depth - 1 - reduce, -alpha - 1, -alpha, True, ply + 1, deadline)
            score = -score
            if alpha < score < beta:
                score, _ = ab_search(board, depth - 1, -beta, -score, True, ply + 1, deadline)
                score = -score

        board.pop()

        if score > best_val:
            best_val = score
            best_move = move
        if score > alpha:
            alpha = score
        if alpha >= beta:
            STATS.cutoffs += 1
            # Killer and history updates on beta cutoffs
            killers = KILLERS.setdefault(ply, [])
            if move not in killers:
                killers.insert(0, move)
                del killers[2:]
            key_hist = (board.turn, move.from_square, move.to_square)
            HISTORY[key_hist] = HISTORY.get(key_hist, 0) + depth * depth
            break

    # Store to TT
    flag = EXACT
    if best_val <= alpha_orig:
        flag = UPPERBOUND
    elif best_val >= beta:
        flag = LOWERBOUND
    TT[key] = TTEntry(depth, flag, best_val, best_move)
    if ply == 0:
        STATS.stop()
        logger.info("Alpha-beta: %s", STATS.summary())
        plot_profile_stats(STATS, filename="ab_profile.png")

    return best_val, best_move


# Shared killer and history tables
KILLERS: Dict[int, List[chess.Move]] = {}
HISTORY: Dict[Tuple[int, int, int], int] = {}


def search(board: chess.Board, depth: int, deadline: float | None = None) -> Tuple[float, Optional[chess.Move]]:
    """Convenience wrapper around :func:`ab_search` with fresh tables."""
    STATS.start()

    TT.clear()
    KILLERS.clear()
    HISTORY.clear()

    alpha, beta = -INF, INF
    best_score, best_move = -INF, None

    moves = order_moves(board, generate_moves(board), KILLERS, HISTORY, 0, None)
    for move in moves:
        if deadline is not None and time.monotonic() >= deadline:
            break
        board.push(move)
        score, _ = ab_search(board, depth - 1, -beta, -alpha, True, 1, deadline)
        score = -score
        board.pop()
        if score > best_score:
            best_score, best_move = score, move
        if score > alpha:
            alpha = score

    STATS.stop()
    logger.info("Alpha-beta: %s", STATS.summary())
    plot_profile_stats(STATS, filename="ab_profile.png")

    return best_score, best_move


def search_one_shot(board: chess.Board, depth: int) -> Tuple[float, Optional[chess.Move], str]:
    """Run a single search and return profiling information.

    The function returns a tuple ``(score, move, profile)`` where ``profile`` is
    a formatted string containing the top cumulative time entries from the
    profiler.
    """

    prof = cProfile.Profile()
    prof.enable()
    score, move = search(board, depth)
    prof.disable()

    s = io.StringIO()
    stats = pstats.Stats(prof, stream=s).sort_stats("cumulative")
    stats.print_stats(20)
    profile_output = s.getvalue()

    return score, move, profile_output


__all__ = [
    "search",
    "search_one_shot",
    "ab_search",
    "generate_moves",
    "order_moves",
]
