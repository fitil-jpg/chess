"""Wrapper that uses :class:`EvaluationTuner` to evaluate a board.

The agent is deliberately light‑weight; it merely forwards the call to the
provided tuner.  This keeps the focus of the tests on integration rather than
chess logic.
"""


class AgentEvaluator:
    def __init__(self, tuner):
        self.tuner = tuner

    def evaluate(self, board, analyzer):  # pragma: no cover - trivial
        """Return a numeric evaluation score for ``board``."""

        return float(self.tuner.tune(board, analyzer))

