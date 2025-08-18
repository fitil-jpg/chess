"""Hybrid orchestrator that mixes MCTS and alpha-beta search."""

from __future__ import annotations

import random
import chess

from .alpha_beta import search as ab_search
from .mcts import BatchMCTS
from .evaluation import evaluate_board

try:  # optional R evaluation
    from .r_bridge import r_evaluate
except Exception:  # pragma: no cover
    r_evaluate = None  # type: ignore


class HybridOrchestrator:
    """Combine two search techniques and choose between their suggestions."""

    def __init__(
        self,
        color: bool,
        ab_depth: int = 3,
        mcts_simulations: int = 64,
        mix_prob: float = 0.5,
        use_r_eval: bool = False,
    ) -> None:
        self.color = color
        self.ab_depth = ab_depth
        self.mcts_simulations = mcts_simulations
        self.mix_prob = mix_prob
        self.mcts = BatchMCTS()
        self.use_r_eval = use_r_eval and r_evaluate is not None

    def _evaluate(self, board: chess.Board) -> float:
        if self.use_r_eval:
            try:
                return r_evaluate(board.fen())
            except Exception:
                pass
        return evaluate_board(board)

    def choose_move(self, board: chess.Board) -> tuple[chess.Move | None, str]:
        if board.turn != self.color:
            return None, "not my turn"
        # Compute candidate moves
        mcts_move, _ = self.mcts.search(board, n_simulations=self.mcts_simulations)
        ab_score, ab_move = ab_search(board, self.ab_depth)
        candidates: list[tuple[chess.Move | None, float, str]] = []
        if mcts_move is not None:
            b = board.copy()
            b.push(mcts_move)
            candidates.append((mcts_move, self._evaluate(b), "MCTS"))
        if ab_move is not None:
            b = board.copy()
            b.push(ab_move)
            candidates.append((ab_move, self._evaluate(b), "AB"))
        if not candidates:
            return None, "no moves"
        # With probability mix_prob choose higher eval, otherwise random between them
        if random.random() < self.mix_prob and len(candidates) >= 2:
            move, _, tag = max(candidates, key=lambda x: x[1])
            return move, f"HYBRID({tag})"
        move, _, tag = random.choice(candidates)
        return move, f"HYBRID({tag})"

