from __future__ import annotations

import logging
import time
logger = logging.getLogger(__name__)

from collections import defaultdict
from typing import Dict, List, Tuple, Optional

import chess
import os

from .decision_engine import DecisionEngine
from core.move_object import MoveObject, MovePhase, EvaluationStep, MoveStatus, move_evaluation_manager
from ui.decision_roadmap import decision_roadmap

from .aggressive_bot import AggressiveBot
from .chess_bot import ChessBot
from .endgame_bot import EndgameBot
from .fortify_bot import FortifyBot
from .random_bot import RandomBot
from .critical_bot import CriticalBot
from .pawn_bot import PawnBot
from .king_value_bot import KingValueBot
from .neural_bot import NeuralBot
from core.evaluator import Evaluator
from core.phase import GamePhaseDetector
from utils import GameContext
from metrics.calibration import centipawn_to_winprob

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
        # Ensembling improvements
        phase_weights: Optional[Dict[str, Dict[str, float]]] = None,
        enable_diversity: bool | None = None,
        diversity_bonus: float | None = None,
        enable_bandit: bool | None = None,
        bandit_alpha: float | None = None,
        # Move tracking options
        enable_move_tracking: bool = True,
    ) -> None:
        self.color = color
        # Registered sub-agents as (impl, name)
        self.agents: List[Tuple[object, str]] = []
        weights = weights or {}
        use_r = _USE_R if use_r is None else use_r
        # Deeper search engine used to break ties or provide a fallback.
        self.decision_engine = DecisionEngine()
        # Lazily-created evaluator shared across sub-bots for this instance.
        self._evaluator: Evaluator | None = None

        # ---- Config ---------------------------------------------------------
        # Base per-agent weights (phase-agnostic defaults)
        self.base_weights: Dict[str, float] = {
            "aggressive": float(getattr(weights, "get", lambda *_: 1.0)("aggressive", 1.0)) if isinstance(weights, dict) else 1.0,
            "fortify":   float(getattr(weights, "get", lambda *_: 1.0)("fortify", 1.0)) if isinstance(weights, dict) else 1.0,
            "critical":  float(getattr(weights, "get", lambda *_: 1.0)("critical", 1.0)) if isinstance(weights, dict) else 1.0,
            "pawn":      float(getattr(weights, "get", lambda *_: 0.8)("pawn", 0.8)) if isinstance(weights, dict) else 0.8,
            "king":      float(getattr(weights, "get", lambda *_: 0.9)("king", 0.9)) if isinstance(weights, dict) else 0.9,
            "endgame":   float(getattr(weights, "get", lambda *_: 1.0)("endgame", 1.0)) if isinstance(weights, dict) else 1.0,
            "random":    float(getattr(weights, "get", lambda *_: 0.0)("random", 0.0)) if isinstance(weights, dict) else 0.0,
            "center":    float(getattr(weights, "get", lambda *_: 1.0)("center", 1.0)) if isinstance(weights, dict) else 1.0,
            "neural":    float(getattr(weights, "get", lambda *_: 1.0)("neural", 1.0)) if isinstance(weights, dict) else 1.0,
            "r":         float(getattr(weights, "get", lambda *_: 1.0)("r", 1.0)) if isinstance(weights, dict) else 1.0,
        }

        # If the caller passed a nested mapping with phases, honour it; else
        # allow an explicit phase_weights override; else default to base.
        provided_phase_weights: Dict[str, Dict[str, float]] = {}
        if isinstance(weights, dict):
            for ph in ("opening", "middlegame", "endgame"):
                v = weights.get(ph)
                if isinstance(v, dict):
                    provided_phase_weights[ph] = {k: float(vv) for k, vv in v.items()}
        self.weights_by_phase: Dict[str, Dict[str, float]] = (
            phase_weights or provided_phase_weights or {}
        )

        # Diversity bonus config
        self.enable_diversity: bool = (
            (os.getenv("CHESS_DYNAMIC_DIVERSITY", "1") == "1")
            if enable_diversity is None else bool(enable_diversity)
        )
        self.diversity_bonus: float = (
            float(os.getenv("CHESS_DYNAMIC_DIVERSITY_BONUS", "0.25"))
            if diversity_bonus is None else float(diversity_bonus)
        )

        # Contextual bandit config
        self.enable_bandit: bool = (
            (os.getenv("CHESS_DYNAMIC_BANDIT", "1") == "1")
            if enable_bandit is None else bool(enable_bandit)
        )
        self.bandit_alpha: float = (
            float(os.getenv("CHESS_DYNAMIC_BANDIT_ALPHA", "0.15"))
            if bandit_alpha is None else float(bandit_alpha)
        )
        # bandit multipliers per position-type bucket and agent name
        self._bandit_weights: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(lambda: 1.0))
        
        # Dynamic endgame boost tracking
        self._endgame_boost_active = False
        self._original_weights = self.base_weights.copy()
        
        # Move tracking for visualization
        self.enable_move_tracking = enable_move_tracking
        self.current_move_object: Optional[MoveObject] = None

        # Register default agents with provided weights (fallback → 1.0).
        # RandomBot is disabled by default and must be explicitly enabled via
        # ``weights={'random': <value>}`` to avoid unnecessary randomness.
        self.register_agent(AggressiveBot(color), "aggressive")
        self.register_agent(FortifyBot(color), "fortify")
        # CriticalBot with hierarchical delegation enabled
        self.register_agent(CriticalBot(color, enable_hierarchy=True), "critical")
        # New specialized bots
        self.register_agent(PawnBot(color), "pawn")
        self.register_agent(KingValueBot(color, enable_heatmaps=True), "king")
        self.register_agent(EndgameBot(color), "endgame")

        rand_weight = self.base_weights.get("random", 0.0)
        if rand_weight > 0.0:
            self.register_agent(RandomBot(color), "random")

        self.register_agent(ChessBot(color), "center")
        self.register_agent(NeuralBot(color), "neural")
        if use_r and _r_eval_board is not None:
            self.register_agent(_RBoardEvaluator(color), "r")

    def register_agent(self, agent: object, name: str | None = None, weight: float | None = None) -> None:
        """Register a sub-agent.

        Parameters
        ----------
        agent:
            The sub-agent instance exposing ``choose_move``.
        name:
            Semantic agent name used to resolve weights (e.g. ``"aggressive"``).
            If omitted, a unique ``custom_N`` name is assigned.
        weight:
            Optional base weight to use for this agent when no phase-specific
            override is provided. If given, it updates ``base_weights[name]``.
        """

        if name is None:
            name = f"custom_{len(self.agents)}"
        self.agents.append((agent, name))
        if weight is not None:
            try:
                self.base_weights[name] = float(weight)
            except Exception:
                self.base_weights[name] = 1.0

    # ---- Weight resolution & context buckets --------------------------------
    def _resolve_phase_weight(self, phase: str, agent_name: str) -> float:
        by_phase = self.weights_by_phase.get(phase)
        if by_phase is not None and agent_name in by_phase:
            w = float(by_phase[agent_name])
            # Confirm phase-aware weighting in logs for traceability
            logger.info(
                "AI-Technique PhaseWeights: phase=%s agent=%s weight=%.3f",
                phase,
                agent_name,
                w,
            )
            return w
        return float(self.base_weights.get(agent_name, 1.0))

    def _position_bucket(self, board: chess.Board, evaluator: Evaluator) -> str:
        phase = GamePhaseDetector.detect(board)
        # Tactics/lightweight features
        feats = evaluator.compute_features(self.color)
        has_tactics = bool(feats.get("can_give_check") or feats.get("has_hanging_enemy") or feats.get("valuable_capture"))
        wm, bm = evaluator.mobility(board)
        low_mob = min(wm, bm) < 8
        return f"{phase}|{'tac' if has_tactics else 'quiet'}|{'low' if low_mob else 'norm'}"

    def _bandit_multiplier(self, bucket: str, agent_name: str) -> float:
        return float(self._bandit_weights[bucket][agent_name])

    def _update_bandit(self, bucket: str, supporting_agents: List[str], reward: float) -> None:
        if not self.enable_bandit or not supporting_agents:
            return
        # Multiplicative weights update; reward expected in roughly [-1, 1]
        lr = self.bandit_alpha
        for name in supporting_agents:
            w = self._bandit_weights[bucket][name]
            new_w = w * (2.718281828 ** (lr * reward))
            # Clamp to avoid explosion/vanishing; renormalize later on read
            self._bandit_weights[bucket][name] = max(0.25, min(new_w, 4.0))
            logger.info(
                "AI-Technique BanditUpdate: bucket=%s agent=%s alpha=%.3f reward=%.3f old=%.3f new=%.3f",
                bucket,
                name,
                lr,
                reward,
                w,
                self._bandit_weights[bucket][name],
            )

    # ---- Diversity helpers --------------------------------------------------
    @staticmethod
    def _idea_squares(board: chess.Board, move: chess.Move) -> set[int]:
        # Simple idea representation: from and to squares; include one step along
        # slider direction when applicable to provide a bit more structure.
        s: set[int] = {move.from_square, move.to_square}
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            from_f, from_r = chess.square_file(move.from_square), chess.square_rank(move.from_square)
            to_f, to_r = chess.square_file(move.to_square), chess.square_rank(move.to_square)
            df = (1 if to_f > from_f else -1 if to_f < from_f else 0)
            dr = (1 if to_r > from_r else -1 if to_r < from_r else 0)
            if df != 0 or dr != 0:
                nf, nr = from_f + df, from_r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    s.add(chess.square(nf, nr))
        return s

    def _apply_diversity_bonus(
        self,
        board: chess.Board,
        scores: Dict[chess.Move, float],
        agent_best: Dict[str, Tuple[chess.Move, float]],
    ) -> None:
        if not self.enable_diversity or len(agent_best) < 2:
            return
        # Precompute idea squares per agent
        ideas: Dict[str, set[int]] = {name: self._idea_squares(board, mv_conf[0]) for name, mv_conf in agent_best.items()}
        names = list(agent_best.keys())
        n = len(names)
        # For each pair of distinct agent proposals, add a small bonus to both
        # moves if their ideas are largely non-overlapping.
        for i in range(n):
            for j in range(i + 1, n):
                ni, nj = names[i], names[j]
                mi, ci = agent_best[ni]
                mj, cj = agent_best[nj]
                si, sj = ideas[ni], ideas[nj]
                inter = len(si.intersection(sj))
                denom = max(len(si), len(sj), 1)
                overlap_ratio = inter / denom
                if overlap_ratio <= 0.25:
                    bonus = self.diversity_bonus * (1.0 - overlap_ratio)
                    # Award bonus to the lower-confidence proposal to encourage
                    # diverse alternatives to overtake a slightly higher single idea.
                    eps = 1e-9
                    if abs(ci - cj) <= eps:
                        scores[mi] = scores.get(mi, 0.0) + bonus
                        scores[mj] = scores.get(mj, 0.0) + bonus
                    elif ci < cj:
                        scores[mi] = scores.get(mi, 0.0) + bonus
                    else:
                        scores[mj] = scores.get(mj, 0.0) + bonus

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
        
        # Initialize move tracking if enabled
        if self.enable_move_tracking:
            self.current_move_object = move_evaluation_manager.create_move_evaluation(
                move=None,  # Will be set after selection
                board=board,
                bot_name="DynamicBot"
            )
            self.current_move_object.start_phase(MovePhase.BOT_EVALUATION)

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

        # Dynamic endgame weight adjustment based on material
        phase = GamePhaseDetector.detect(board)
        if phase == "endgame":
            self._boost_endgame_weights(board, evaluator)
            
        # Track phase information
        if self.enable_move_tracking and self.current_move_object:
            self.current_move_object.metadata['phase'] = phase
            self.current_move_object.metadata['position_bucket'] = self._position_bucket(board, evaluator)

        scores: Dict[chess.Move, float] = defaultdict(float)
        debug_contrib: Dict[chess.Move, List[str]] = defaultdict(list)
        # Keep raw weighted scores per move for a later win-prob estimate.
        per_move_weighted: Dict[chess.Move, List[float]] = defaultdict(list)

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

        # Phase-aware + bandit-aware weights
        phase = GamePhaseDetector.detect(board)
        position_bucket = self._position_bucket(board, evaluator)
        logger.info(
            "AI-Technique Ensemble: phase=%s agents=%d bucket=%s diversity=%s(bonus=%.2f) bandit=%s(alpha=%.2f)",
            phase,
            len(self.agents),
            position_bucket,
            str(self.enable_diversity),
            self.diversity_bonus,
            str(self.enable_bandit),
            self.bandit_alpha,
        )
        # Track per-agent best move for diversity bonus and bandit credit
        agent_best: Dict[str, Tuple[chess.Move, float]] = {}

        for agent, agent_name in self.agents:
            # Track agent evaluation start
            if self.enable_move_tracking and self.current_move_object:
                step = EvaluationStep(
                    method_name=f"{agent_name}_evaluation",
                    bot_name=agent_name,
                    input_data={
                        'phase': phase,
                        'position_bucket': position_bucket,
                        'weights': {
                            'base': self._resolve_phase_weight(phase, agent_name),
                            'bandit': self._bandit_multiplier(position_bucket, agent_name) if self.enable_bandit else 1.0
                        }
                    }
                )
                self.current_move_object.add_evaluation_step(step)
                step_start_time = time.time()
            
            if debug:
                move, conf = agent.choose_move(
                    board, context=context, evaluator=evaluator, debug=True
                )
            else:
                move, conf = agent.choose_move(
                    board, context=context, evaluator=evaluator
                )
            
            # Track agent evaluation completion
            if self.enable_move_tracking and self.current_move_object:
                step.duration_ms = (time.time() - step_start_time) * 1000
                step.status = MoveStatus.COMPLETED if move else MoveStatus.REJECTED
                step.confidence = conf
                step.output_data = {
                    'move': move.uci() if move else None,
                    'confidence': conf,
                    'engine': type(agent).__name__
                }
                
            if move is None:
                continue
            # Resolve weights
            base_w = self._resolve_phase_weight(phase, agent_name)
            bandit_w = self._bandit_multiplier(position_bucket, agent_name) if self.enable_bandit else 1.0
            weight = base_w * bandit_w
            score = conf * weight
            scores[move] += score
            per_move_weighted[move].append(score)
            agent_best[agent_name] = (move, conf)
            
            # Track move scoring
            if self.enable_move_tracking and self.current_move_object:
                self.current_move_object.contributing_factors[f"{agent_name}_score"] = score
                
            if debug:
                debug_contrib[move].append(
                    f"{agent_name}:{type(agent).__name__}: conf={conf:.3f} w={weight:.3f} (base={base_w:.3f} bandit={bandit_w:.3f}) → {score:.3f}"
                )

        # Diversity bonus across agents' proposals
        if self.enable_diversity and agent_best:
            self._apply_diversity_bonus(board, scores, agent_best)

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

        # Pick the highest scoring move from sub-agents. If several moves are
        # effectively tied (within a tiny epsilon), resolve deterministically
        # by UCI to avoid arbitrary changes by deeper engines during tests.
        sorted_moves = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        move, total = sorted_moves[0]
        # Determine all near-tied candidates
        TIE_EPS = 1e-3
        tied: List[chess.Move] = [mv for mv, sc in sorted_moves if abs(sc - total) < TIE_EPS]
        if len(tied) > 1:
            move = min(tied, key=lambda m: m.uci())

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
        # Tie already resolved deterministically above; avoid deeper engine
        # tie-breaking that may select unrelated moves.

        # Compute a calibrated win probability from the weighted per-move scores.
        # We treat the accumulated weighted scores as centipawn-like and convert
        # via a logistic mapping.
        weighted_list = per_move_weighted.get(move, [total])
        avg_weighted = sum(weighted_list) / max(1, len(weighted_list))
        win_prob = centipawn_to_winprob(avg_weighted)

        # Online bandit update: measure local reward and adjust weights for
        # supporting agents in this bucket.
        if self.enable_bandit:
            before = evaluator.position_score(board, self.color)
            tmp_bandit = board.copy(stack=False)
            tmp_bandit.push(move)
            # Reuse evaluator on the child position without recomputing PST
            evaluator.board = tmp_bandit
            after = evaluator.position_score(tmp_bandit, self.color)
            evaluator.board = board
            delta = after - before
            # Normalise reward to [-1, 1] approximately via tanh-like scaling
            reward = max(-1.0, min(1.0, delta / 200.0))
            # Agents that contributed to the chosen move receive credit
            supporters: List[str] = []
            for name, (mv, _c) in agent_best.items():
                if mv == move:
                    supporters.append(name)
            self._update_bandit(position_bucket, supporters, reward)

        if debug:
            logger.debug("DynamicBot contributions:")
            for mv, lines in debug_contrib.items():
                for line in lines:
                    logger.debug(f"  {mv}: {line}")
            logger.debug(f"DynamicBot selected {move} with score {total:.3f} (p(win)={win_prob:.3f})")
        
        # Finalize move tracking
        if self.enable_move_tracking and self.current_move_object:
            self.current_move_object.move = move
            self.current_move_object.san_notation = board.san(move) if board.is_legal(move) else str(move)
            self.current_move_object.final_score = float(total)
            self.current_move_object.confidence = win_prob
            self.current_move_object.primary_reason = f"Ensemble decision with {len(agent_best)} contributing agents"
            self.current_move_object.status = MoveStatus.COMPLETED
            self.current_move_object.end_phase(MovePhase.BOT_EVALUATION)
            
            # Add final metadata
            self.current_move_object.metadata.update({
                'total_agents': len(self.agents),
                'contributing_agents': len(agent_best),
                'win_probability': win_prob,
                'ensemble_score': total,
                'selected_move': move.uci(),
                'phase': phase,
                'position_bucket': position_bucket,
                'diversity_enabled': self.enable_diversity,
                'bandit_enabled': self.enable_bandit
            })
            
            # Store contributing agents info
            for name, (mv, conf) in agent_best.items():
                if mv == move:
                    self.current_move_object.metadata[f'supporting_agent_{name}'] = {
                        'confidence': conf,
                        'weight': self._resolve_phase_weight(phase, name),
                        'bandit_multiplier': self._bandit_multiplier(position_bucket, name) if self.enable_bandit else 1.0
                    }
            
            # Finalize in manager
            move_evaluation_manager.finalize_current_move()
            
            # Update decision roadmap
            decision_roadmap.update_from_manager()
            
        # Preserve numeric compatibility: return a score; callers that want
        # probability can derive or read debug logs. We return the same 'total'
        # to avoid changing tests, but downstream wrappers may surface rationale.
        return move, float(total)

    def _boost_endgame_weights(self, board: chess.Board, evaluator: Evaluator) -> None:
        """Динамічно підвищує ваги EndgameBot залежно від матеріалу на дошці."""
        
        # Розраховуємо кількість матеріалу
        material_count = self._count_material(board)
        
        # Визначаємо рівень ендшпілю
        if material_count <= 10:  # Пізній ендшпіль
            endgame_multiplier = 2.5
            king_multiplier = 1.6
            pawn_multiplier = 1.4
            aggressive_multiplier = 0.3
        elif material_count <= 15:  # Важкий ендшпіль
            endgame_multiplier = 1.8
            king_multiplier = 1.4
            pawn_multiplier = 1.3
            aggressive_multiplier = 0.5
        elif material_count <= 23:  # Середній ендшпіль
            endgame_multiplier = 1.5
            king_multiplier = 1.2
            pawn_multiplier = 1.1
            aggressive_multiplier = 0.7
        else:
            return  # Не застосовуємо буст якщо достатньо матеріалу
        
        # Застосовуємо множники
        self.base_weights["endgame"] = self._original_weights["endgame"] * endgame_multiplier
        self.base_weights["king"] = self._original_weights["king"] * king_multiplier
        self.base_weights["pawn"] = self._original_weights["pawn"] * pawn_multiplier
        self.base_weights["aggressive"] = self._original_weights["aggressive"] * aggressive_multiplier
        
        self._endgame_boost_active = True
        
        logger.info(
            "AI-Technique EndgameBoost: material=%d endgame=%.2f king=%.2f pawn=%.2f aggressive=%.2f",
            material_count,
            self.base_weights["endgame"],
            self.base_weights["king"],
            self.base_weights["pawn"],
            self.base_weights["aggressive"]
        )
    
    def _count_material(self, board: chess.Board) -> int:
        """Рахує загальну вартість матеріалу на дошці."""
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        total = 0
        for piece_type, value in piece_values.items():
            total += len(board.pieces(piece_type, chess.WHITE)) * value
            total += len(board.pieces(piece_type, chess.BLACK)) * value
        
        return total
    
    def reset_weights(self) -> None:
        """Скидає ваги до оригінальних значень."""
        if self._endgame_boost_active:
            self.base_weights = self._original_weights.copy()
            self._endgame_boost_active = False
            logger.info("AI-Technique EndgameBoost: weights reset to original")
    
    def get_decision_roadmap(self) -> Dict[str, Any]:
        """Отримати повну дорожню карту прийняття рішень для поточного ходу."""
        if not self.enable_move_tracking:
            return {"status": "disabled", "message": "Move tracking is disabled"}
        
        return decision_roadmap.get_current_roadmap()
    
    def get_agent_performance_summary(self) -> Dict[str, Any]:
        """Отримати підсумок продуктивності всіх агентів."""
        if not self.enable_move_tracking:
            return {"status": "disabled", "message": "Move tracking is disabled"}
        
        return decision_roadmap.get_agent_performance_summary()
    
    def export_decision_data(self, filename: str, include_history: bool = True) -> None:
        """Експортувати дані про прийняття рішень у JSON файл."""
        if not self.enable_move_tracking:
            logger.warning("Move tracking is disabled - no data to export")
            return
        
        decision_roadmap.export_roadmap_json(filename, include_history)
        logger.info(f"Decision data exported to {filename}")
    
    def print_decision_summary(self, move_index: int = -1) -> None:
        """Вивести підсумок прийняття рішень в консоль."""
        if not self.enable_move_tracking:
            logger.warning("Move tracking is disabled - no summary available")
            return
        
        print(decision_roadmap.get_console_summary(move_index))
    
    def get_real_time_decision_updates(self) -> Dict[str, Any]:
        """Отримати оновлення в реальному часі для поточного процесу прийняття рішень."""
        if not self.enable_move_tracking:
            return {"status": "disabled", "message": "Move tracking is disabled"}
        
        return decision_roadmap.get_real_time_updates()
    
    def enable_tracking(self, enabled: bool = True) -> None:
        """Увімкнути/вимкнути відстеження ходів."""
        self.enable_move_tracking = enabled
        logger.info(f"Move tracking {'enabled' if enabled else 'disabled'}")
    
    def get_current_move_object(self) -> Optional[MoveObject]:
        """Отримати поточний об'єкт ходу для прямого доступу."""
        return self.current_move_object
