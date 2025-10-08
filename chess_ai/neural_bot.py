from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

"""Neural-network powered sub-bot using :class:`TorchNet`.

The network is loaded lazily to avoid importing the heavy ``torch`` package
unless the bot is actually queried for a move.  This keeps unit tests lightweight
and maintains API compatibility with other agents.
"""

import chess
import math

from core.evaluator import Evaluator
from utils import GameContext

# Shared network instance reused across bots.  Annotated as a forward reference
# so that importing this module does not require ``torch``.
_SHARED_NET: "TorchNet | None" = None
_NN_CFG: dict | None = None


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

        # Optional shallow search blending (config-driven)
        shallow_depth = 0
        topk = 0
        blend_lambda = 0.5
        global _NN_CFG
        if _NN_CFG is None:
            try:
                import yaml  # type: ignore
                with open("configs/nn.yaml", "r", encoding="utf-8") as fh:
                    _NN_CFG = yaml.safe_load(fh) or {}
            except Exception:
                _NN_CFG = {}
        cfg = _NN_CFG or {}
        try:
            shallow_cfg = cfg.get("shallow_search", {}) or {}
            shallow_depth = int(shallow_cfg.get("depth", 0) or 0)
            topk = int(shallow_cfg.get("topk", 0) or 0)
            blend_lambda = float(shallow_cfg.get("blend_lambda", 0.5) or 0.5)
        except Exception:
            shallow_depth = 0
            topk = 0
            blend_lambda = 0.5

        if shallow_depth > 0 and topk > 0:
            # Select top-k policy candidates
            items = sorted(policy.items(), key=lambda kv: kv[1], reverse=True)[:topk]
            try:
                # Lazy import to avoid heavy cost if unused
                from .hybrid_bot.alpha_beta import search as ab_search
                import chess as _chess
            except Exception:
                ab_search = None  # type: ignore

            scored: list[tuple[chess.Move, float, float]] = []  # (move, policy_p, blended_score)
            for mv, p in items:
                s_norm = 0.0
                if ab_search is not None:
                    tmp = board.copy(stack=False)
                    tmp.push(mv)
                    try:
                        score_cp, _best = ab_search(tmp, shallow_depth)
                    except TypeError:
                        # Fallback to convenience wrapper if signature differs
                        from .hybrid_bot.alpha_beta import search as _search
                        score_cp, _best = _search(tmp, shallow_depth)
                    # Convert centipawn-like score to [-1,1] with soft saturation
                    s_norm = math.tanh(float(score_cp) / 600.0)
                    s_norm = -s_norm  # negate because search is from opponent's turn now
                blended = blend_lambda * float(p) + (1.0 - blend_lambda) * s_norm
                scored.append((mv, float(p), blended))

            if scored:
                scored.sort(key=lambda t: t[2], reverse=True)
                return scored[0][0], float(value)

        # Default: pick highest policy move
        move = max(policy.items(), key=lambda kv: kv[1])[0]
        return move, float(value)