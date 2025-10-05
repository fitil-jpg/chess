# metrics.py

"""Light‑weight evaluation helpers built on top of :mod:`python-chess`.

The :class:`MetricsManager` operates on a :class:`chess.Board` instance and
produces a handful of simple metrics.  The heavy lifting for those metrics lives
in :mod:`metrics_common` so both this module and ``core.metrics`` can delegate to
the same implementation.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure vendored dependencies are importable when this package is used
VENDOR_PATH = Path(__file__).resolve().parents[1] / "vendors"
if str(VENDOR_PATH) not in sys.path:
    sys.path.append(str(VENDOR_PATH))

import chess
from .base_evaluator import MetricEvaluator

from metrics_common import (
    count_attacked_squares as _count_attacked_squares,
    count_defended_pieces as _count_defended_pieces,
    evaluate_center_control as _evaluate_center_control,
    evaluate_king_safety as _evaluate_king_safety,
    evaluate_pawn_structure as _evaluate_pawn_structure,
    evaluate_survivability as _evaluate_survivability,
)


class MetricsManager:
    """Compute a few tiny heuristics for the given board state."""

    def __init__(self, board_state: chess.Board):
        self.board_state = board_state
        self.metrics = {"short_term": {}, "long_term": {}}

    # ------------------------------------------------------------------
    # Metric calculation helpers
    # ------------------------------------------------------------------
    def update_all_metrics(self) -> None:  # pragma: no cover - simple wrapper
        self.metrics["short_term"]["attacked_squares"] = self.count_attacked_squares()
        self.metrics["short_term"]["defended_pieces"] = self.count_defended_pieces()
        self.metrics["short_term"]["survivability"] = self.evaluate_survivability()
        self.metrics["long_term"]["center_control"] = self.evaluate_center_control()
        self.metrics["long_term"]["king_safety"] = self.evaluate_king_safety()
        self.metrics["long_term"]["pawn_structure_stability"] = self.evaluate_pawn_structure()

    def count_attacked_squares(self) -> int:
        return _count_attacked_squares(self.board_state)

    def count_defended_pieces(self) -> int:
        return _count_defended_pieces(self.board_state)

    def evaluate_center_control(self) -> int:
        return _evaluate_center_control(self.board_state)

    def evaluate_king_safety(self) -> int:
        return _evaluate_king_safety(self.board_state)

    def evaluate_pawn_structure(self) -> int:
        return _evaluate_pawn_structure(self.board_state)

    def evaluate_survivability(self):
        return _evaluate_survivability(self.board_state)

    def get_metrics(self):  # pragma: no cover - trivial accessor
        return self.metrics


__all__ = ["MetricsManager", "MetricEvaluator"]

