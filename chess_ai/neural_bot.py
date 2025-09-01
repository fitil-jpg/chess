from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

"""Neural-network powered sub-bot using :class:`TorchNet`.

The network is loaded lazily to avoid importing the heavy ``torch`` package
unless the bot is actually queried for a move.  This keeps unit tests lightweight
and maintains API compatibility with other agents.
"""

import chess

from core.evaluator import Evaluator
from utils import GameContext

# Shared network instance reused across bots.  Annotated as a forward reference
# so that importing this module does not require ``torch``.
_SHARED_NET: "TorchNet | None" = None


class NeuralBot:
    """Bot that selects moves based on a neural network policy."""

    def __init__(self, color: bool, net: "TorchNet" | None = None) -> None:
        self.color = color
        self._net = net

    # ------------------------------------------------------------------
    def _get_net(self) -> "TorchNet":
        """Return a network instance, creating one on first use.

        If PyTorch or the network configuration is unavailable, a stub network
        returning empty policies and zero value is used.  This mirrors the
        behaviour of other simple agents and keeps tests independent from the
        ``torch`` dependency.
        """

        global _SHARED_NET
        if self._net is not None:
            return self._net
        if _SHARED_NET is None:
            try:  # pragma: no cover - exercised indirectly
                from .nn import TorchNet

                _SHARED_NET = TorchNet.from_config()
            except Exception:  # ImportError or config issues
                class _StubNet:
                    def predict_many(self, boards):
                        return [({}, 0.0) for _ in boards]

                _SHARED_NET = _StubNet()
        self._net = _SHARED_NET
        return self._net

    # ------------------------------------------------------------------
    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return a move and confidence derived from the network.

        Parameters
        ----------
        board: chess.Board
            Position to analyse.
        context: GameContext | None, optional
            Included for API compatibility (unused).
        evaluator: Evaluator | None, optional
            Included for API compatibility (unused).
        debug: bool, optional
            Unused flag for interface parity.
        """

        net = self._get_net()
        policy, value = net.predict_many([board])[0]
        if not policy:
            return None, float(value)
        move = max(policy.items(), key=lambda kv: kv[1])[0]
        return move, float(value)