from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

import chess

from .aggressive_bot import AggressiveBot
from .chess_bot import ChessBot
from .endgame_bot import EndgameBot
from .fortify_bot import FortifyBot
from .random_bot import RandomBot
from core.evaluator import Evaluator
from utils import GameContext


_SHARED_EVALUATOR: Evaluator | None = None


class DynamicBot:
    """Meta-agent that aggregates suggestions from registered sub-bots.

    Each registered agent is paired with a weight.  When choosing a move the
    confidence of every agent is multiplied by its weight and accumulated per
    move.  The move with the highest total score is returned.
    """

    def __init__(self, color: bool, *, weights: Dict[str, float] | None = None):
        self.color = color
        self.agents: List[Tuple[object, float]] = []
        weights = weights or {}

        # Register default agents with provided weights (fallback → 1.0)
        self.register_agent(AggressiveBot(color), weights.get("aggressive", 1.0))
        self.register_agent(FortifyBot(color), weights.get("fortify", 1.0))
        self.register_agent(EndgameBot(color), weights.get("endgame", 1.0))
        self.register_agent(RandomBot(color), weights.get("random", 1.0))
        self.register_agent(ChessBot(color), weights.get("center", 1.0))

    def register_agent(self, agent: object, weight: float = 1.0) -> None:
        """Register a sub-agent with an optional weight."""

        self.agents.append((agent, weight))

    def choose_move(
        self,
        board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Gather candidate moves from each sub-bot and choose the best.

        A single :class:`GameContext` and :class:`Evaluator` instance are
        constructed once and shared with all sub-agents to avoid duplicated
        work.
        """

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        if context is None:
            material = evaluator.material_diff(self.color)
            white_moves, black_moves = evaluator.mobility(board)
            mobility_score = white_moves - black_moves
            if not self.color:
                mobility_score = -mobility_score
            king_safety_score = Evaluator.king_safety(board, self.color)
            context = GameContext(
                material_diff=material,
                mobility=mobility_score,
                king_safety=king_safety_score,
            )

        scores: Dict[chess.Move, float] = defaultdict(float)
        debug_contrib: Dict[chess.Move, List[str]] = defaultdict(list)

        for agent, weight in self.agents:
            if debug:
                move, conf = agent.choose_move(
                    board, context=context, evaluator=evaluator, debug=True
                )
            else:
                move, conf = agent.choose_move(
                    board, context=context, evaluator=evaluator
                )
            if move is None:
                continue
            score = conf * weight
            scores[move] += score
            if debug:
                debug_contrib[move].append(
                    f"{type(agent).__name__}: conf={conf:.3f} w={weight:.3f} → {score:.3f}"
                )

        if not scores:
            return None, 0.0

        move = max(scores.items(), key=lambda kv: kv[1])[0]
        total = scores[move]
        if debug:
            print("DynamicBot contributions:")
            for mv, lines in debug_contrib.items():
                for line in lines:
                    print(f"  {mv}: {line}")
            print(f"DynamicBot selected {move} with score {total:.3f}")
        return move, total
