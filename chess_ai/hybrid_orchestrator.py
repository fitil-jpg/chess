"""Hybrid orchestrator mixing batched MCTS with alpha-beta validation.

This module provides :class:`HybridOrchestrator` which first runs a batched
Monte Carlo tree search to obtain a set of candidate moves.  The top-K moves
are then validated using a classic alpha-beta search combined with the optional
R-based evaluation.  Scores from both stages are normalised and mixed to select
the final move.  Diagnostic information for visualisation or debugging is
returned alongside the chosen move.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import os
import chess

from .batched_mcts import BatchedMCTS, Node
from .hybrid_bot.alpha_beta import search as ab_search
from .hybrid_bot.evaluation import evaluate_position


# ---------------------------------------------------------------------------
# Optional R-based evaluation
# ---------------------------------------------------------------------------

_USE_R = os.getenv("CHESS_USE_R") == "1"
if _USE_R:
    try:  # pragma: no cover - rpy2 may be absent
        from .hybrid_bot.r_bridge import eval_board
    except Exception:  # pragma: no cover - optional dependency
        eval_board = None  # type: ignore
else:  # R evaluation disabled
    eval_board = None  # type: ignore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _EvalNet:
    """Minimal network used when no neural net is supplied.

    The network exposes a ``predict_many`` method returning a uniform policy
    over legal moves and the static evaluation of the board.  This mirrors the
    interface expected by :class:`BatchedMCTS`.
    """

    def predict_many(
        self, boards: List[chess.Board]
    ) -> List[Tuple[Dict[chess.Move, float], float]]:
        results: List[Tuple[Dict[chess.Move, float], float]] = []
        for b in boards:
            legal = list(b.legal_moves)
            policy: Dict[chess.Move, float] = {}
            if legal:
                pri = 1.0 / len(legal)
                policy = {m: pri for m in legal}
            value = evaluate_position(b)
            results.append((policy, value))
        return results


@dataclass
class _Candidate:
    """Container keeping intermediate scores for a single move."""

    move: chess.Move
    mcts: float
    ab: float
    r: float
    mcts_norm: float = 0.0
    ab_norm: float = 0.0
    mixed: float = 0.0

    def as_dict(self) -> Dict[str, float | str]:
        """Return a dictionary representation for diagnostics."""
        return {
            "move": self.move.uci(),
            "mcts": self.mcts,
            "ab": self.ab,
            "r": self.r,
            "mcts_norm": self.mcts_norm,
            "ab_norm": self.ab_norm,
            "mixed": self.mixed,
        }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class HybridOrchestrator:
    """Select moves by mixing MCTS and alpha-beta evaluations."""

    def __init__(
        self,
        color: bool,
        *,
        net=None,
        ab_depth: int = 3,
        mcts_simulations: int = 64,
        top_k: int = 3,
        lam: float = 0.5,
        batch_size: int = 8,
    ) -> None:
        self.color = color
        self.ab_depth = ab_depth
        self.mcts_simulations = mcts_simulations
        self.top_k = top_k
        self.lam = lam
        self.batch_size = batch_size
        if net is None:
            net = _EvalNet()
        self.net = net
        self.mcts = BatchedMCTS(net)

    # ------------------------------------------------------------------
    def _r_eval(self, board: chess.Board) -> float:
        """Evaluate ``board`` using the optional R bridge if available."""
        if eval_board is not None:
            try:
                return eval_board(board)
            except Exception:
                pass
        return evaluate_position(board)

    @staticmethod
    def _norm(vals: List[float]) -> List[float]:
        """Normalise ``vals`` to ``[0, 1]`` with protection against constants."""
        mn, mx = min(vals), max(vals)
        if abs(mx - mn) < 1e-9:
            return [0.5 for _ in vals]
        return [(v - mn) / (mx - mn) for v in vals]

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------
    def choose_move(self, board: chess.Board) -> Tuple[chess.Move | None, Dict[str, Any]]:
        """Return the final move and diagnostic information."""
        if board.turn != self.color:
            return None, {"candidates": [], "chosen": None, "mcts_first": None}

        root = Node(board.copy())
        _move, root = self.mcts.search_batch(
            root,
            n_simulations=self.mcts_simulations,
            batch_size=self.batch_size,
        )
        children = sorted(root.children.items(), key=lambda kv: kv[1].n, reverse=True)
        if not children:
            return None, {"candidates": [], "chosen": None, "mcts_first": None}

        candidates: List[_Candidate] = []
        for move, node in children[: self.top_k]:
            b = board.copy()
            b.push(move)
            depth = max(1, self.ab_depth - 1)
            ab_val, _ = ab_search(b, depth)
            ab_val = -ab_val
            r_val = self._r_eval(b)
            if b.turn != self.color:
                r_val = -r_val
            ab_score = (ab_val + r_val) / 2.0
            candidates.append(_Candidate(move, node.q(), ab_score, r_val))

        mcts_norms = self._norm([c.mcts for c in candidates])
        ab_norms = self._norm([c.ab for c in candidates])
        for cand, m_n, a_n in zip(candidates, mcts_norms, ab_norms):
            cand.mcts_norm = m_n
            cand.ab_norm = a_n
            cand.mixed = self.lam * m_n + (1 - self.lam) * a_n

        chosen = max(candidates, key=lambda c: c.mixed)
        mcts_first = max(candidates, key=lambda c: c.mcts)
        diag = {
            "candidates": [c.as_dict() for c in candidates],
            "chosen": chosen.move.uci(),
            "mcts_first": mcts_first.move.uci(),
        }
        return chosen.move, diag


__all__ = ["HybridOrchestrator"]

