from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

import chess
import os

from .aggressive_bot import AggressiveBot
from .chess_bot import ChessBot
from .endgame_bot import EndgameBot
from .fortify_bot import FortifyBot
from .random_bot import RandomBot
from .critical_bot import CriticalBot
from .neural_bot import NeuralBot
from core.evaluator import Evaluator
from utils import GameContext

_USE_R = os.getenv("CHESS_USE_R") == "1"
if _USE_R:
    try:  # pragma: no cover - optional dependency
        from .hybrid_bot.r_bridge import eval_board as _r_eval_board
    except Exception:  # rpy2 may be missing
        _r_eval_board = None  # type: ignore
else:  # R evaluation disabled
    _r_eval_board = None  # type: ignore


_SHARED_EVALUATOR: Evaluator | None = None


class _RBoardEvaluator:
    """Lightweight wrapper around the optional R-based evaluator."""

    def __init__(self, color: bool):
        self.color = color

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        if _r_eval_board is None:
            return None, 0.0

        best_move: chess.Move | None = None
        best_score = float("-inf")
        for mv in board.legal_moves:
            tmp = board.copy(stack=False)
            tmp.push(mv)
            try:  # pragma: no cover - rpy2 may be absent
                score = _r_eval_board(tmp)
            except Exception:
                return None, 0.0
            score = float(score if self.color == chess.WHITE else -score)
            if score > best_score:
                best_score = score
                best_move = mv
        return best_move, best_score


class DynamicBot:
    """Meta-agent that aggregates suggestions from registered sub-bots.

    Each registered agent is paired with a weight.  When choosing a move the
    confidence of every agent is multiplied by its weight and accumulated per
    move.  The move with the highest total score is returned.  The optional
    R-based evaluator can be enabled via the ``CHESS_USE_R`` environment
    variable or by passing ``use_r=True`` when constructing the bot.
    """

    def __init__(
        self,
        color: bool,
        *,
        weights: Dict[str, float] | None = None,
        use_r: bool | None = None,
    ) -> None:
        self.color = color
        self.agents: List[Tuple[object, float]] = []
        weights = weights or {}
        use_r = _USE_R if use_r is None else use_r

        # Register default agents with provided weights (fallback → 1.0)
        self.register_agent(AggressiveBot(color), weights.get("aggressive", 1.0))
        self.register_agent(FortifyBot(color), weights.get("fortify", 1.0))
        self.register_agent(CriticalBot(color), weights.get("critical", 1.0))
        self.register_agent(EndgameBot(color), weights.get("endgame", 1.0))
        self.register_agent(RandomBot(color), weights.get("random", 1.0))
        self.register_agent(ChessBot(color), weights.get("center", 1.0))
        self.register_agent(NeuralBot(color), weights.get("neural", 1.0))
        if use_r and _r_eval_board is not None:
            self.register_agent(_RBoardEvaluator(color), weights.get("r", 1.0))

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
