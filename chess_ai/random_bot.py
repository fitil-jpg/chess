import logging
logger = logging.getLogger(__name__)

import random
import math

from core.evaluator import Evaluator
from utils import GameContext


_SHARED_EVALUATOR: Evaluator | None = None
# Small tweak applied when mobility differs between the sides.
# The bot slightly prefers positions where it has more mobility and
# de-emphasises ones with less, based only on the sign of the mobility.
# The positive and negative adjustments differ by ``2 * MOBILITY_FACTOR``.
MOBILITY_FACTOR = 0.01


class RandomBot:
    def __init__(self, color: bool, *, temperature: float = 1.0):
        self.color = color
        # Temperature controls exploration in softmax sampling. Higher values
        # make the distribution flatter; lower values make it greedier.
        self.temperature = max(1e-6, float(temperature))

    def choose_move(
        self,
        board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return a temperature-weighted random move with blunder filtering.

        Parameters
        ----------
        board: chess.Board
            Position to analyse.
        context: GameContext | None, optional
            Shared game context (unused).
        evaluator: Evaluator | None, optional
            Reusable evaluator.  A shared one is created if ``None``.
        debug: bool, optional
            Unused flag for API compatibility.
        """

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        moves = sorted(board.legal_moves, key=lambda m: m.uci())
        if not moves:
            return None, 0.0

        # Evaluate all moves and mark risky ones (potential outright blunders).
        # Import lazily to avoid any circular import sensitivities.
        try:
            from .risk_analyzer import RiskAnalyzer  # type: ignore
            risk = RiskAnalyzer()
        except Exception:
            risk = None  # Fallback: no risk filtering if analyzer unavailable

        candidates: list[tuple[float, object, bool]] = []
        # (score, move, is_risky)
        for mv in moves:
            tmp = board.copy(stack=False)
            tmp.push(mv)
            score = float(evaluator.position_score(tmp, self.color))
            is_risky = False
            if risk is not None:
                try:
                    # Risk check uses the current board; it pushes/pops internally.
                    is_risky = risk.is_risky(board, mv)
                except Exception:
                    is_risky = False
            candidates.append((score, mv, is_risky))

        # Filter out risky moves if there exists at least one non-risky option.
        safe = [c for c in candidates if not c[2]]
        pool = safe if safe else candidates

        # Temperature-weighted sampling via softmax.
        T = self.temperature
        max_score = max(s for s, _, _ in pool)
        weights = [math.exp((s - max_score) / T) for s, _, _ in pool]
        total_w = sum(weights)
        # Guard against numerical issues
        if not math.isfinite(total_w) or total_w <= 0:
            # Fallback to greedy
            chosen_score, chosen_move, _ = max(pool, key=lambda t: t[0])
        else:
            r = random.random() * total_w
            acc = 0.0
            chosen_score = pool[-1][0]
            chosen_move = pool[-1][1]
            for (w, (s, mv, _)) in zip(weights, pool):
                acc += w
                if r <= acc:
                    chosen_score = s
                    chosen_move = mv
                    break

        conf = chosen_score
        if context is not None and context.mobility != 0:
            bias = 1 if context.mobility > 0 else -1
            conf += bias * MOBILITY_FACTOR
        return chosen_move, float(conf)
