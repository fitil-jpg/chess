"""Hybrid orchestrator blending MCTS and alpha-beta search.

This module defines :class:`HybridOrchestrator` which performs a Monte
Carlo tree search to gather the top-K candidate moves. Each candidate is
validated by running an alpha-beta search and by invoking the optional
R-based evaluator. The normalised scores from the MCTS and alpha-beta
steps are combined using a λ-mix to determine the final move. Diagnostic
information, including the list of evaluated candidates, the move selected
after mixing, and the best MCTS move before mixing, is returned to aid
visualisation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import logging
logger = logging.getLogger(__name__)

import chess
import os
import time

from .alpha_beta import search as ab_search
from .mcts import BatchMCTS
from .evaluation import evaluate_position

_USE_R = os.getenv("CHESS_USE_R") == "1"
if _USE_R:
    try:  # optional R evaluation
        from .r_bridge import eval_board
    except Exception:  # pragma: no cover - rpy2 may be absent
        eval_board = None  # type: ignore
else:  # R evaluation disabled
    eval_board = None  # type: ignore


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


class HybridOrchestrator:
    """Select moves by mixing MCTS and alpha-beta evaluations."""

    def __init__(
        self,
        color: bool,
        ab_depth: int = 3,
        mcts_simulations: int = 64,
        top_k: int = 3,
        lam: float = 0.5,
    ) -> None:
        self.color = color
        self.ab_depth = ab_depth
        self.mcts_simulations = mcts_simulations
        self.top_k = top_k
        self.lam = lam
        self.mcts = BatchMCTS()

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------
    def _r_eval(self, board: chess.Board) -> float:
        """Evaluate ``board`` using the optional R bridge if available."""
        if eval_board is not None:
            try:
                return eval_board(board)
            except Exception:
                # Fall back to the Python evaluator if the R call fails.
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
    def choose_move(
        self,
        board: chess.Board,
        *,
        plot: bool = False,
        plot_title: str | None = None,
        plot_path: str | None = None,
        time_budget_s: float | None = None,
    ) -> Tuple[chess.Move | None, Dict[str, Any]]:
        """Return the final move and optional visualisation.

        Parameters
        ----------
        board:
            Current game state.
        plot:
            If ``True``, :func:`plot_orchestrator_diag` is invoked to visualise
            the diagnostic information returned by this method.
        plot_title:
            Optional title passed to :func:`plot_orchestrator_diag`.
        plot_path:
            If provided, the generated figure is saved to this path.
        time_budget_s:
            Optional per-move time budget in seconds. The orchestrator splits
            this across MCTS and alpha-beta checks and ensures a safe fallback
            when the deadline is reached.
        """
        if board.turn != self.color:
            return None, {"candidates": [], "chosen": None, "mcts_first": None}

        # Per-move time management
        deadline: float | None = None
        if time_budget_s is not None:
            deadline = time.monotonic() + time_budget_s

        # Perform MCTS and gather top-K candidates by visit count
        mcts_deadline: float | None = None
        if deadline is not None:
            # Allocate ~60% of the remaining budget to MCTS
            remaining = max(0.0, deadline - time.monotonic())
            mcts_deadline = time.monotonic() + 0.6 * remaining
        _, root = self.mcts.search(
            board,
            n_simulations=self.mcts_simulations,
            deadline=mcts_deadline,
        )
        children = sorted(root.children.items(), key=lambda kv: kv[1].n, reverse=True)
        if not children:
            # Fallback: pick any legal move quickly
            first = next(iter(board.legal_moves), None)
            return first, {"candidates": [], "chosen": None, "mcts_first": None}

        candidates: List[_Candidate] = []
        for move, node in children[: self.top_k]:
            b = board.copy()
            b.push(move)
            depth = max(1, self.ab_depth - 1)
            # Distribute remaining time evenly across candidates
            ab_deadline: float | None = None
            if deadline is not None:
                remaining = max(0.0, deadline - time.monotonic())
                per = remaining / max(1, self.top_k)
                ab_deadline = time.monotonic() + per
            ab_val, _ = ab_search(b, depth, deadline=ab_deadline)
            ab_val = -ab_val  # convert to our perspective
            r_val = self._r_eval(b)
            if b.turn != self.color:
                r_val = -r_val
            ab_score = (ab_val + r_val) / 2
            candidates.append(_Candidate(move, node.q(), ab_score, r_val))

        # Normalise scores
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

        if plot:
            from .viz import plot_orchestrator_diag

            title = plot_title
            if title is None:
                colour = "White" if self.color == chess.WHITE else "Black"
                title = f"{colour} move {board.fullmove_number}"
            plot_orchestrator_diag(diag, title=title, save_path=plot_path)

        # Ensure safe fallback if time was exceeded
        if deadline is not None and time.monotonic() >= deadline:
            return mcts_first.move, diag
        return chosen.move, diag


__all__ = ["HybridOrchestrator"]
