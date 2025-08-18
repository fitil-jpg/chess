"""
bot_agent.py
Призначення: зібрані боти + фасад BotAgent для простого імпорту у в’ювер.
ОНОВЛЕННЯ:
 - Додано клас BotAgent (фасад), щоб `from chess_ai.bot_agent import BotAgent` працювало без помилок.
 - Вбудовано FortifyBot у DynamicBot (SAFE CHECK → FORTIFY → AGGRESSIVE → ENDGAME → LOW MOBILITY → CENTER).
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, List
import random
import chess
from .evaluator import Evaluator
from .constants import MATERIAL_DIFF_THRESHOLD, KING_SAFETY_THRESHOLD
from utils import GameContext

__all__ = [
    "BotAgent",
    "DynamicBot",
    "FortifyBot",
    "AggressiveBot",
    "ChessBot",
    "EndgameBot",
    "RandomBot",
]

# --- Зовнішні боти (fallback-заглушки, якщо модулів немає у вашому пакеті) ---
try:
    from .chess_bot import ChessBot  # «Center»
except Exception:
    class ChessBot:
        def __init__(self, color: bool): self.color = color
        def choose_move(self, board: chess.Board, context: GameContext | None = None, debug: bool = True):
            moves = list(board.legal_moves)
            m = random.choice(moves) if moves else None
            return m, "ChessBot(STUB): random"

try:
    from .endgame_bot import EndgameBot
except Exception:
    class EndgameBot:
        def __init__(self, color: bool): self.color = color
        def choose_move(self, board: chess.Board, context: GameContext | None = None, debug: bool = True):
            moves = list(board.legal_moves)
            m = random.choice(moves) if moves else None
            return m, "EndgameBot(STUB): random"

try:
    from .random_bot import RandomBot
except Exception:
    class RandomBot:
        def __init__(self, color: bool): self.color = color
        def choose_move(self, board: chess.Board, context: GameContext | None = None, debug: bool = True):
            moves = list(board.legal_moves)
            m = random.choice(moves) if moves else None
            return m, "RandomBot(STUB): random"


# --- Спільні константи/утиліти ---
CENTER_16 = {
    chess.C3, chess.D3, chess.E3, chess.F3,
    chess.C4, chess.D4, chess.E4, chess.F4,
    chess.C5, chess.D5, chess.E5, chess.F5,
    chess.C6, chess.D6, chess.E6, chess.F6,
}


# --- Aggressive (проста фіч-модель) ---
class Scorer:
    def __init__(self):
        self.weights: Dict[str, int] = {
            "capture_hanging": 100,
            "capture_defended": 20,
            "check": 35,
            "develop": 70,
            "nothing": 1,
        }
    def score(self, features: Dict[str, Any]) -> int:
        if features.get("is_capture") and features.get("target_is_hanging"):
            return self.weights["capture_hanging"]
        if features.get("gives_check"):
            base = self.weights["check"]
            if features.get("is_safe_check"):
                base += 5
            return base
        if features.get("is_capture"):
            return self.weights["capture_defended"]
        if features.get("develops_piece"):
            return self.weights["develop"]
        return self.weights["nothing"]

class _FeatureExtractor:
    @staticmethod
    def _opponent(color: bool) -> bool:
        return not color
    @staticmethod
    def _is_hanging_target(board: chess.Board, move: chess.Move, mover_color: bool) -> bool:
        if not board.is_capture(move):
            return False
        opp = not mover_color
        defenders = board.attackers(opp, move.to_square)
        return len(defenders) == 0
    @staticmethod
    def _is_safe_check(board: chess.Board, move: chess.Move, mover_color: bool) -> bool:
        temp = board.copy(stack=False)
        temp.push(move)
        if not temp.is_check():
            return False
        defenders = temp.attackers(mover_color, move.to_square)
        return len(defenders) > 0
    @staticmethod
    def _develops(board: chess.Board, move: chess.Move, mover_color: bool) -> bool:
        piece = board.piece_at(move.from_square)
        if not piece: return False
        if piece.piece_type not in (chess.KNIGHT, chess.BISHOP): return False
        rank_from = chess.square_rank(move.from_square)
        if (mover_color is chess.WHITE and rank_from != 0) or (mover_color is chess.BLACK and rank_from != 7):
            return False
        return move.to_square in CENTER_16
    def extract(self, board: chess.Board, move: chess.Move, mover_color: bool) -> Dict[str, Any]:
        return {
            "is_capture": board.is_capture(move),
            "target_is_hanging": self._is_hanging_target(board, move, mover_color),
            "gives_check": board.gives_check(move),
            "is_safe_check": self._is_safe_check(board, move, mover_color),
            "develops_piece": self._develops(board, move, mover_color),
        }

class AggressiveBot:
    def __init__(self, color: bool):
        self.color = color
        self.scorer = Scorer()
        self.fx = _FeatureExtractor()
    def choose_move(self, board: chess.Board, context: GameContext | None = None, debug: bool = True):
        best_s = -10**9
        best: List[Tuple[chess.Move, Dict[str, Any]]] = []
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color: continue
            feats = self.fx.extract(board, m, self.color)
            s = self.scorer.score(feats)
            if s > best_s: best_s, best = s, [(m, feats)]
            elif s == best_s: best.append((m, feats))
        if not best: return None, "AggressiveBot: no legal moves"
        move, feats = random.choice(best)
        return move, f"AggressiveBot: score={best_s} feats={ {k:v for k,v in feats.items() if v} }"


# --- FortifyBot (стає на найбільш захищену клітину з пріоритетом develop) ---
class FortifyBot:
    """
    Вибирає хід за максимальною «захищеністю» клітини призначення:
      defense_density = defenders(to) - attackers(to).
    Плюси: develop, capture, подвійні пішаки суперника, прорідження «щитка» пішаків перед його королем.
    Вибір фігури для develop (дефолтні ваги): KNIGHT > BISHOP > ROOK > QUEEN > PAWN > KING.
    """
    PIECE_DEV_WEIGHTS = {
        chess.KNIGHT: 1.0,
        chess.BISHOP: 0.9,
        chess.ROOK:   0.6,
        chess.QUEEN:  0.5,
        chess.PAWN:   0.4,
        chess.KING:   0.0,
    }
    def __init__(self, color: bool, *, safe_only: bool = False, weights: Optional[Dict[str, float]] = None):
        self.color = color
        self.safe_only = safe_only
        self.W = {
            "defense_density": 5.0,
            "defenders": 0.5,
            "develop": 3.0,
            "capture": 2.5,
            "opp_doubled_delta": 4.0,
            "opp_shield_delta": 5.0,
        }
        if weights: self.W.update(weights)

    def choose_move(self, board: chess.Board, context: GameContext | None = None, debug: bool = True) -> Tuple[Optional[chess.Move], str]:
        m, info = self._best(board)
        if debug and m is not None:
            reason = (
                f"FortifyBot: {board.san(m)} | dens={info['defense_density']} "
                f"def={info['defenders']} att={info['attackers']} | "
                f"dev={int(info['develop'])} cap={int(info['is_capture'])} | "
                f"doubledΔ={info['opp_doubled_delta']} shieldΔ={info['opp_shield_delta']} | "
                f"by={info.get('piece_type')}"
            )
            return m, reason
        return m, "FortifyBot"

    def _best(self, board: chess.Board) -> Tuple[Optional[chess.Move], Dict[str, Any]]:
        best = None
        best_score = float("-inf")
        best_info: Dict[str, Any] = {}
        if board.turn != self.color:
            return None, {}
        opp = not self.color
        before_doubled = self._count_doubled_pawns(board, opp)
        before_shield = self._king_pawn_shield_count(board, opp)
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color: continue
            tmp = board.copy(stack=False); tmp.push(m)
            to_sq = m.to_square
            defenders = len(tmp.attackers(self.color, to_sq))
            attackers = len(tmp.attackers(opp, to_sq))
            dens = defenders - attackers
            if self.safe_only and attackers > 0:
                continue
            develops = self._develops(board, m, p)
            is_capture = board.is_capture(m)
            after_doubled = self._count_doubled_pawns(tmp, opp)
            after_shield  = self._king_pawn_shield_count(tmp, opp)
            score = (
                self.W["defense_density"] * dens +
                self.W["defenders"] * defenders +
                self.W["develop"] * (self.PIECE_DEV_WEIGHTS.get(p.piece_type, 0.0) if develops else 0.0) +
                self.W["capture"] * (1 if is_capture else 0) +
                self.W["opp_doubled_delta"] * max(0, after_doubled - before_doubled) +
                self.W["opp_shield_delta"]  * max(0, before_shield - after_shield)
            )
            if score > best_score:
                best_score = score
                best = m
                best_info = {
                    "defense_density": dens, "defenders": defenders, "attackers": attackers,
                    "develop": develops, "is_capture": is_capture,
                    "opp_doubled_delta": max(0, after_doubled - before_doubled),
                    "opp_shield_delta": max(0, before_shield - after_shield),
                    "piece_type": p.piece_type
                }
        return best, best_info

    # --- евристики ---
    def _develops(self, board: chess.Board, m: chess.Move, p: chess.Piece) -> bool:
        rank_from = chess.square_rank(m.from_square)
        back_rank = (0 if self.color else 7)
        in_center = m.to_square in CENTER_16
        if p.piece_type in (chess.KNIGHT, chess.BISHOP):
            return (rank_from == back_rank) and in_center
        if p.piece_type == chess.ROOK:
            return (rank_from == back_rank)  # умовно «виводимо»
        if p.piece_type == chess.QUEEN:
            return (rank_from == back_rank) and (chess.square_distance(m.from_square, m.to_square) <= 2)
        if p.piece_type == chess.PAWN:
            start_rank = 1 if self.color else 6
            return rank_from == start_rank
        return False

    def _count_doubled_pawns(self, board: chess.Board, color: bool) -> int:
        files = [0]*8
        for sq, piece in board.piece_map().items():
            if piece.color == color and piece.piece_type == chess.PAWN:
                files[chess.square_file(sq)] += 1
        return sum(1 for c in files if c >= 2)

    def _king_pawn_shield_count(self, board: chess.Board, color: bool) -> int:
        ksq = board.king(color)
        if ksq is None: return 0
        kf = chess.square_file(ksq)
        ranks = (1, 2) if color == chess.WHITE else (6, 5)
        total = 0
        for f in (kf-1, kf, kf+1):
            if 0 <= f <= 7:
                for r in ranks:
                    sq = chess.square(f, r)
                    p = board.piece_at(sq)
                    if p and p.color == color and p.piece_type == chess.PAWN:
                        total += 1
        return total


# --- DynamicBot: комбінатор стратегій ---
class DynamicBot:
    """Bot that switches strategy based on simple board metrics."""

    def __init__(
        self,
        color: bool,
        *,
        material_diff_threshold: int = MATERIAL_DIFF_THRESHOLD,
        king_safety_threshold: int = KING_SAFETY_THRESHOLD,
    ):
        self.center = ChessBot(color)
        self.endgame = EndgameBot(color)
        self.random = RandomBot(color)
        self.aggressive = AggressiveBot(color)
        self.fortify = FortifyBot(color)
        self.color = color
        self.material_diff_threshold = material_diff_threshold
        self.king_safety_threshold = king_safety_threshold

    def _select_agent(self, context: GameContext):
        choices: List[Tuple[int, Any]] = []
        if context.material_diff > self.material_diff_threshold:
            choices.append((context.material_diff - self.material_diff_threshold, self.aggressive))
        if context.king_safety < self.king_safety_threshold:
            choices.append((self.king_safety_threshold - context.king_safety, self.fortify))

        if choices:
            choices.sort(key=lambda x: x[0], reverse=True)
            return choices[0][1]
        return self.center

    def choose_move(self, board: chess.Board, context: GameContext | None = None, debug: bool = True):
        if context is None:
            evaluator = Evaluator(board)
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
        agent = self._select_agent(context)
        return agent.choose_move(board, context=context, debug=debug)


# --- ФАСАД: BotAgent ---
class BotAgent:
    """
    Єдиний вхід для в’ювера/зовнішнього коду.
    Використання:
        agent = BotAgent(color=True, mode="dynamic")
        move, reason = agent.choose_move(board, debug=True)
    Доступні режими: "dynamic" (дефолт), "fortify", "aggressive", "center", "endgame", "random".
    """
    def __init__(self, color: bool, *, mode: str = "dynamic", **kwargs):
        self.color = color
        self.mode = mode.lower()
        self.impl = self._make_impl(color, self.mode, **kwargs)

    def _make_impl(self, color: bool, mode: str, **kwargs):
        if mode == "dynamic":
            return DynamicBot(
                color,
                material_diff_threshold=kwargs.get("material_diff_threshold", MATERIAL_DIFF_THRESHOLD),
                king_safety_threshold=kwargs.get("king_safety_threshold", KING_SAFETY_THRESHOLD),
            )
        if mode == "fortify":
            return FortifyBot(color, **{k: v for k, v in kwargs.items() if k in ("safe_only", "weights")})
        if mode == "aggressive":
            return AggressiveBot(color)
        if mode == "center":
            return ChessBot(color)
        if mode == "endgame":
            return EndgameBot(color)
        if mode == "random":
            return RandomBot(color)
        # fallback → dynamic
        return DynamicBot(color)

    def choose_move(self, board: chess.Board, debug: bool = True):
        evaluator = Evaluator(board)
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
        return self.impl.choose_move(board, context=context, debug=debug)
