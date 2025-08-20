# metrics.py

"""Mirror of :mod:`metrics` for the :mod:`core` package."""

from __future__ import annotations

import chess

from metrics_common import (
    count_attacked_squares as _count_attacked_squares,
    count_defended_pieces as _count_defended_pieces,
    evaluate_center_control as _evaluate_center_control,
    evaluate_king_safety as _evaluate_king_safety,
    evaluate_pawn_structure as _evaluate_pawn_structure,
)


class MetricsManager:
    """Compute a few tiny heuristics for the given board state."""

    def __init__(self, board_state: chess.Board):
        self.board_state = board_state
        self.metrics = {"short_term": {}, "long_term": {}}

    def update_all_metrics(self) -> None:  # pragma: no cover - thin wrapper
        self.metrics["short_term"]["attacked_squares"] = self.count_attacked_squares()
        self.metrics["short_term"]["defended_pieces"] = self.count_defended_pieces()
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

    def get_metrics(self):  # pragma: no cover - trivial accessor
        return self.metrics


class BoardMetrics:
    """Minimal metrics helper used in tests."""

    def __init__(self):
        self._metrics = {}

    def update_from_board(self, board, analyzer):  # pragma: no cover - trivial
        white = len(board.get_pieces('white'))
        black = len(board.get_pieces('black'))
        self._metrics['material_balance'] = white - black

    def get_metrics(self):  # pragma: no cover - trivial
        return self._metrics


__all__ = ["MetricsManager", "BoardMetrics"]

