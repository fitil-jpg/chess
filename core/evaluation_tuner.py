"""Simple evaluation tuner used in tests.

The real project likely contains sophisticated tuning logic.  For the purposes
of the unit tests in this kata we only need an object that exposes a
``tune`` method returning a numeric score.
"""

import logging
logger = logging.getLogger(__name__)

class EvaluationTuner:
    def tune(self, board, analyzer):  # pragma: no cover - placeholder logic
        """Return a basic evaluation score.

        The implementation intentionally does very little; it simply returns 0.
        The method exists so that :class:`AgentEvaluator` can delegate to it
        without accessing board internals.
        """

        return 0
