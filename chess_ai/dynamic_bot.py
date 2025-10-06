from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from collections import defaultdict
from typing import Dict, List, Tuple

import chess
import os

from .decision_engine import DecisionEngine

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

    A :class:`DecisionEngine` instance performs a deeper search to refine
    ambiguous results or act as a fallback when the lightweight sub-agents do
    not provide a confident choice.  For a Monte Carlo tree search counterpart
    see :class:`chess_ai.batched_mcts.BatchedMCTS`.  Both engines are showcased
    together in ``tests/run_hybrid_demo.py``.
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
        # Deeper search engine used to break ties or provide a fallback.
        self.decision_engine = DecisionEngine()
        # Lazily-created evaluator shared across sub-bots for this instance.
        self._evaluator: Evaluator | None = None

        # Register default agents with provided weights (fallback → 1.0).
        # RandomBot is disabled by default and must be explicitly enabled via
        # ``weights={'random': <value>}`` to avoid unnecessary randomness.
        self.register_agent(AggressiveBot(color), weights.get("aggressive", 1.0))
        self.register_agent(FortifyBot(color), weights.get("fortify", 1.0))
        self.register_agent(CriticalBot(color), weights.get("critical", 1.0))
        self.register_agent(EndgameBot(color), weights.get("endgame", 1.0))

        rand_weight = weights.get("random", 0.0)
        if rand_weight > 0.0:
            self.register_agent(RandomBot(color), rand_weight)

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
        work.  When the combined scores do not yield a clear favourite the
        :class:`DecisionEngine` is invoked to perform a deeper variant search
        and break ties.
        """

        evaluator = evaluator or self._evaluator
        if evaluator is None:
            evaluator = self._evaluator = Evaluator(board)
        else:
            evaluator.board = board

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

        # Detect the most critical opponent piece so that moves neutralising
        # dangerous forks can be prioritised.  We consider only knight threats
        # that scored the extra fork bonus inside :meth:`Evaluator.criticality`.
        critical = evaluator.criticality(board, self.color)
        fork_threat_score: int | None = None
        if critical:
            top_sq, top_score = critical[0]
            piece = board.piece_at(top_sq)
            if piece and piece.piece_type == chess.KNIGHT and top_score >= 10:
                fork_threat_score = top_score

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

        # Boost moves that reduce the detected fork threat.
        if fork_threat_score is not None:
            bonus = 5.0
            for mv in list(scores.keys()):
                tmp = board.copy(stack=False)
                tmp.push(mv)
                new_crit = evaluator.criticality(tmp, self.color)
                new_score = new_crit[0][1] if new_crit else 0
                if new_score < fork_threat_score:
                    scores[mv] += bonus
                    if debug:
                        debug_contrib[mv].append(f"fork_bonus={bonus:.3f}")

        if not scores:
            # No agent produced a move; fall back to a deeper search.
            engine_move = self.decision_engine.choose_best_move(board)
            return (engine_move, 0.0) if engine_move else (None, 0.0)

        # Pick the highest scoring move from sub-agents.
        sorted_moves = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        move, total = sorted_moves[0]

        # Avoid steering into an imminent threefold repetition unless it is
        # clearly the only non-disadvantageous option. If the chosen move
        # repeats, consult the deeper decision engine which includes a
        # tolerance and tactical pyramid (check > capture > attack) to select
        # a different move when reasonable.
        tmp = board.copy(stack=False)
        tmp.push(move)
        repeats = tmp.is_repetition(3)
        tmp.pop()
        if repeats:
            engine_move = self.decision_engine.choose_best_move(board)
            if engine_move is not None:
                move = engine_move
                total = scores.get(engine_move, total)

        # If top candidates are too close, ask the decision engine to
        # perform a deeper search to break the tie.
        if len(sorted_moves) > 1:
            second_score = sorted_moves[1][1]
            if abs(total - second_score) < 1e-3:
                engine_move = self.decision_engine.choose_best_move(board)
                if engine_move is not None:
                    move = engine_move
                    total = scores.get(engine_move, total)

        if debug:
            logger.debug("DynamicBot contributions:")
            for mv, lines in debug_contrib.items():
                for line in lines:
                    logger.debug(f"  {mv}: {line}")
            logger.debug(f"DynamicBot selected {move} with score {total:.3f}")
        return move, total
