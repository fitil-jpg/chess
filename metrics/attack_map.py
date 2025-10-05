from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Tuple

import chess


AttackCounts = Tuple[Tuple[int, ...], Tuple[int, ...]]  # (white_counts, black_counts)


def _coerce_key(value) -> int:
    """Coerce various key shapes (int/tuple/bytes/str) to a stable int.

    Older versions of python-chess may return a tuple for the private
    ``_transposition_key`` helper. We hash non-int values to obtain a compact
    integer key suitable for our LRU dictionary.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        return hash(value)
    try:
        return hash(tuple(value))
    except TypeError:
        return hash(repr(value))


def _position_key(board: chess.Board) -> int:
    """Return a stable key representing the current position.

    Prefers python-chess's transposition key when available, falling back to
    hashing the full FEN string otherwise.
    """
    # python-chess >= 1.12
    if hasattr(board, "transposition_key"):
        tk = board.transposition_key  # method in newer versions; alias in tests for older
        if callable(tk):
            return _coerce_key(tk())  # type: ignore[no-any-return]
        return _coerce_key(tk)  # pragma: no cover - defensive; some versions expose property
    # Older python-chess (private API)
    if hasattr(board, "_transposition_key"):
        return _coerce_key(board._transposition_key())  # type: ignore[attr-defined]
    # Fallback: hash the full FEN
    return hash(board.fen())


def _compute_attack_counts(board: chess.Board) -> AttackCounts:
    """Compute number of attackers for each square for both colours.

    Returns
    -------
    (white_counts, black_counts)
        Each a 64-length tuple where index = square (0..63).
    """
    white_counts = [0] * 64
    black_counts = [0] * 64

    for sq in chess.SQUARES:
        white_counts[sq] = len(board.attackers(chess.WHITE, sq))
        black_counts[sq] = len(board.attackers(chess.BLACK, sq))

    return tuple(white_counts), tuple(black_counts)


class AttackMapCache:
    """Tiny per-process cache for attack maps keyed by position.

    The cache is independent of any particular board instance and keyed by a
    position key (transposition key when available). This makes successive
    re-evaluations across plies or repeated positions very cheap.
    """

    def __init__(self, maxsize: int = 4096) -> None:
        self.maxsize = int(maxsize)
        self._cache: "OrderedDict[int, AttackCounts]" = OrderedDict()

    def clear(self) -> None:
        self._cache.clear()

    def get(self, board: chess.Board) -> AttackCounts:
        key = _position_key(board)
        cached = self._cache.get(key)
        if cached is not None:
            # LRU bump
            self._cache.move_to_end(key)
            return cached

        result = _compute_attack_counts(board)
        self._cache[key] = result
        # Enforce max size (simple LRU)
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)
        return result


# Module-level cache suitable for most callers
_GLOBAL_CACHE = AttackMapCache()


def attack_count_per_square(board: chess.Board) -> Dict[bool, Tuple[int, ...]]:
    """Return per-square attacker counts for both colours with caching.

    Parameters
    ----------
    board
        Current :class:`chess.Board`.

    Returns
    -------
    Dict[bool, Tuple[int, ...]]
        Mapping keyed by ``chess.WHITE`` and ``chess.BLACK`` to 64-length tuples
        of attacker counts per square.
    """
    white, black = _GLOBAL_CACHE.get(board)
    return {chess.WHITE: white, chess.BLACK: black}


__all__ = ["attack_count_per_square", "AttackMapCache"]
