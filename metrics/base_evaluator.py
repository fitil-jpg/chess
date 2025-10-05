from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import chess


class MetricEvaluator(ABC):
    """Abstract base for lightweight board metric evaluators.

    Subclasses implement :meth:`evaluate` to compute one or more metric values
    for the provided :class:`chess.Board` state.
    """

    @abstractmethod
    def evaluate(self, board: chess.Board) -> Any:
        """Compute and return metric(s) for ``board``.

        Parameters
        ----------
        board:
            The board position to evaluate.

        Returns
        -------
        Any
            A metric value or a structure of values, defined by subclasses.
        """
        raise NotImplementedError


__all__ = ["MetricEvaluator"]
