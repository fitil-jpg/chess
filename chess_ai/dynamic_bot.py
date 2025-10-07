from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from collections import defaultdict
from typing import Dict, List, Tuple, Any
import math

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
from core.phase import GamePhaseDetector

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
        weights: Dict[str, float] | Dict[str, Dict[str, float]] | None = None,
        use_r: bool | None = None,
    ) -> None:
        self.color = color
        # Registered agents along with their base weights provided at registration time.
        self.agents: List[Tuple[object, float]] = []
        weights = weights or {}
        use_r = _USE_R if use_r is None else use_r
        # Deeper search engine used to break ties or provide a fallback.
        self.decision_engine = DecisionEngine()
        # Lazily-created evaluator shared across sub-bots for this instance.
        self._evaluator: Evaluator | None = None

        # Optional phase-aware weights: if a dict with phase keys is provided, use it.
        # Structure: {"opening"|"middlegame"|"endgame": {family: weight, ...}}
        self.weights_by_phase: Dict[str, Dict[str, float]] = {}
        if any(k in weights for k in ("opening", "middlegame", "endgame")):
            # type: ignore[assignment]
            self.weights_by_phase = {  # type: ignore[dict-item]
                k: dict(v) for k, v in ((weights or {}).items()) if k in ("opening", "middlegame", "endgame")  # type: ignore[union-attr]
            }  # type: ignore[assignment]
        # Diversity multiplier strength per extra unique family supporting a move.
        self.diversity_lambda: float = 0.08
        # Bandit parameters and storage (per position-type key, per family theta)
        self._bandit_theta: Dict[str, Dict[str, float]] = {}
        self._bandit_eta: float = 0.05
        self._bandit_reward_scale: float = 100.0

        # Register default agents with provided weights (fallback → 1.0).
        # RandomBot is disabled by default and must be explicitly enabled via
        # ``weights={'random': <value>}`` to avoid unnecessary randomness.
        self.register_agent(AggressiveBot(color), float((weights.get("aggressive", 1.0) if isinstance(weights, dict) else 1.0)))
        self.register_agent(FortifyBot(color), float((weights.get("fortify", 1.0) if isinstance(weights, dict) else 1.0)))
        self.register_agent(CriticalBot(color), float((weights.get("critical", 1.0) if isinstance(weights, dict) else 1.0)))
        self.register_agent(EndgameBot(color), float((weights.get("endgame", 1.0) if isinstance(weights, dict) else 1.0)))

        rand_weight = float((weights.get("random", 0.0) if isinstance(weights, dict) else 0.0))
        if rand_weight > 0.0:
            self.register_agent(RandomBot(color), rand_weight)

        self.register_agent(ChessBot(color), float((weights.get("center", 1.0) if isinstance(weights, dict) else 1.0)))
        self.register_agent(NeuralBot(color), float((weights.get("neural", 1.0) if isinstance(weights, dict) else 1.0)))
        if use_r and _r_eval_board is not None:
            self.register_agent(_RBoardEvaluator(color), float((weights.get("r", 1.0) if isinstance(weights, dict) else 1.0)))

    def register_agent(self, agent: object, weight: float = 1.0) -> None:
        """Register a sub-agent with an optional weight."""
        self.agents.append((agent, float(weight)))

    # ---- helpers for ensembling ----
    @staticmethod
    def _family_name(agent: object) -> str:
        """Return a stable family name for an agent instance."""
        name = type(agent).__name__
        # Map known agents to canonical short family names
        if "Aggressive" in name:
            return "aggressive"
        if "Fortify" in name:
            return "fortify"
        if "Critical" in name:
            return "critical"
        if "Endgame" in name:
            return "endgame"
        if name == "RandomBot":
            return "random"
        if name == "ChessBot":
            return "center"
        if "Neural" in name:
            return "neural"
        if name == "_RBoardEvaluator":
            return "r"
        return name.lower()

    def _position_key(self, board: chess.Board, context: GameContext) -> str:
        """Return a compact key describing current position type for bandit."""
        phase = GamePhaseDetector.detect(board)
        # Bucketize material, safety, mobility
        def bucket(x: float, cuts: List[float]) -> int:
            for i, c in enumerate(cuts):
                if x < c:
                    return i
            return len(cuts)
        mat_b = bucket(float(context.material_diff), [-6, -2, 2, 6])
        saf_b = bucket(float(context.king_safety), [-50, 0, 50])
        mob_b = bucket(float(context.mobility), [-6, -2, 2, 6])
        return f"{phase}|m{mat_b}|s{saf_b}|b{mob_b}"

    def _bandit_multipliers(self, pos_key: str, families: List[str]) -> Dict[str, float]:
        """Compute multiplicative weight multipliers from bandit thetas for families."""
        theta = self._bandit_theta.get(pos_key, {})
        mult: Dict[str, float] = {}
        for fam in families:
            t = float(theta.get(fam, 0.0))
            # Exponentiate to keep positive, clamp to reasonable range
            m = math.exp(max(-2.0, min(2.0, t)))
            mult[fam] = m
        return mult

    def _phase_weight(self, phase: str, family: str) -> float:
        cfg = self.weights_by_phase.get(phase)
        if not cfg:
            return 1.0
        return float(cfg.get(family, 1.0))

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
        supporters: Dict[chess.Move, set[str]] = defaultdict(set)

        # Determine phase and position-type for adaptive weighting.
        phase = GamePhaseDetector.detect(board)
        pos_key = self._position_key(board, context)
        families = [self._family_name(a) for a, _ in self.agents]
        bandit_mult = self._bandit_multipliers(pos_key, families)

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

        for agent, base_weight in self.agents:
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
            fam = self._family_name(agent)
            # Phase-aware and bandit multipliers
            phase_w = self._phase_weight(phase, fam)
            b_mul = bandit_mult.get(fam, 1.0)
            dyn_weight = float(base_weight) * phase_w * b_mul
            score = float(conf) * dyn_weight
            scores[move] += score
            supporters[move].add(fam)
            if debug:
                debug_contrib[move].append(
                    f"{type(agent).__name__}: conf={float(conf):.3f} w={dyn_weight:.3f} (base={base_weight:.2f} phase={phase_w:.2f} bandit={b_mul:.2f}) → {score:.3f}"
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

        # Apply diversity bonus multiplier: more unique families supporting a move → slight boost
        if scores:
            for mv, total in list(scores.items()):
                k = len(supporters.get(mv, set()))
                if k >= 2:
                    multiplier = 1.0 + self.diversity_lambda * float(k - 1)
                    scores[mv] = total * multiplier
                    if debug:
                        debug_contrib[mv].append(f"diversity×={multiplier:.3f} (k={k})")

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

        # Bandit update based on immediate evaluation delta for the selected move.
        try:
            pre = evaluator.position_score(board, self.color)
            tmp = board.copy(stack=False)
            tmp.push(move)
            post = evaluator.position_score(tmp, self.color)
            reward = float(post - pre)
            reward_norm = max(-1.0, min(1.0, reward / self._bandit_reward_scale))
            fams = supporters.get(move, set())
            if fams:
                theta = self._bandit_theta.setdefault(pos_key, {})
                for fam in fams:
                    theta[fam] = float(theta.get(fam, 0.0) + self._bandit_eta * reward_norm)
        except Exception:
            pass

        if debug:
            logger.debug("DynamicBot contributions:")
            for mv, lines in debug_contrib.items():
                for line in lines:
                    logger.debug(f"  {mv}: {line}")
            logger.debug(f"DynamicBot selected {move} with score {total:.3f}")
        return move, total
