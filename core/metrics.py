"""Core-facing metrics helpers.

This module re-exports :class:`metrics.MetricsManager` so core modules can
access the same implementation without duplicating logic.  It also provides a
minimal :class:`BoardMetrics` used in legacy tests.
"""

from __future__ import annotations

from metrics import MetricsManager


class BoardMetrics:
    """Minimal metrics helper used in tests.

    Only a single metric – ``material_balance`` – is tracked.  The method
    :meth:`update_from_board` relies on :meth:`Board.get_pieces` to avoid direct
    access to the board's internal ``pieces`` list.
    """

    def __init__(self):
        self._metrics = {}

    def update_from_board(self, board, analyzer):  # pragma: no cover - trivial
        white = len(board.get_pieces('white'))
        black = len(board.get_pieces('black'))
        self._metrics['material_balance'] = white - black

    def get_metrics(self):  # pragma: no cover - trivial
        return self._metrics


__all__ = ["MetricsManager", "BoardMetrics"]
