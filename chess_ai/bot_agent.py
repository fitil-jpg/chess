"""
bot_agent.py
Зібрані боти + фасади й фабрика для в’ювера/арени.

ОНОВЛЕННЯ:
 - Нормалізовані reason-теги: SAFE_CHECK / COW / DEPTH2 / FORTIFY / AGGRESSIVE / ENDGAME / LOW / CENTER
 - FortifyBot: develop для пішака лише d/e; додано легкий tie-break jitter
 - _MoveOnlyAdapter: get_last_reason() для логування у арені
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, List, Callable, Set
import random
import chess

from core.evaluator import Evaluator
from utils import GameContext

__all__ = [
    "BotAgent",
    "BotAgentLegacy",
    "BotAgentRandom",
    "BotAgentEndgame",
    "BotAgentDynamic",
    "DynamicBot",
    "FortifyBot",
    "AggressiveBot",
    "ChessBot",
    "EndgameBot",
    "RandomBot",
]

# Shared evaluator instance used by DynamicBot to avoid re-initialisation
_SHARED_EVALUATOR: Evaluator | None = None

# ---------- Fallback-и на випадок відсутності реальних модулів ----------
try:
    from .chess_bot import ChessBot  # type: ignore
except Exception:
    class ChessBot:
        def __init__(self, color: bool):
            self.color = color

        def choose_move(
            self,
            board: chess.Board,
            context: GameContext | None = None,
            evaluator: Evaluator | None = None,
            debug: bool = True,
        ):
            moves = list(board.legal_moves)
            m = random.choice(moves) if moves else None
            return m, "CENTER | ChessBot(STUB): random"

try:
    from .endgame_bot import EndgameBot  # type: ignore
except Exception:
    class EndgameBot:
        def __init__(self, color: bool):
            self.color = color

        def choose_move(
            self,
            board: chess.Board,
            context: GameContext | None = None,
            evaluator: Evaluator | None = None,
            debug: bool = True,
        ):
            moves = list(board.legal_moves)
            m = random.choice(moves) if moves else None
            return m, "ENDGAME | EndgameBot(STUB): random"

try:
    from .random_bot import RandomBot  # type: ignore
except Exception:
    class RandomBot:
        def __init__(self, color: bool):
            self.color = color

        def choose_move(
            self,
            board: chess.Board,
            context: GameContext | None = None,
            evaluator: Evaluator | None = None,
            debug: bool = True,
        ):
            moves = list(board.legal_moves)
            m = random.choice(moves) if moves else None
            return m, "LOW | RandomBot(STUB): random"

# ---------- Cow Opening (окремий планер) ----------
class CowOpeningPlanner:
    """
    COW-етапи:
      1) пішаки: e3,d3 (чорним e6,d6)
      2) коні:   g3,b3 (чорним g6,b6)
      3) слони:  білі -> e2,d2,c4,f4 ; чорні -> e7,d7,c5,f5
         (хід ігнорується, якщо робить підвіс наших пішака/фігуру)
    """
    COW_TAG = "COW"

    def __init__(self, color: bool):
        self.color = color
        if color == chess.WHITE:
            self.pawn_targets: Set[int] = {chess.E3, chess.D3}
            self.knight_targets: Set[int] = {chess.G3, chess.B3}
            self.pawn_starts = {chess.E2: chess.E3, chess.D2: chess.D3}
            self.knight_waypoints = {
                chess.G1: [chess.E2, chess.H3, chess.F3],
                chess.B1: [chess.D2, chess.C3],
            }
            self.bishop_targets: Set[int] = {chess.E2, chess.D2, chess.C4, chess.F4}
        else:
            self.pawn_targets = {chess.E6, chess.D6}
            self.knight_targets = {chess.G6, chess.B6}
            self.pawn_starts = {chess.E7: chess.E6, chess.D7: chess.D6}
            self.knight_waypoints = {
                chess.G8: [chess.E7, chess.H6, chess.F6],
                chess.B8: [chess.D7, chess.C6],
            }
            self.bishop_targets = {chess.E7, chess.D7, chess.C5, chess.F5}

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = True,
    ) -> Tuple[Optional[chess.Move], str]:
        if board.turn != self.color:
            return None, f"{self.COW_TAG} | not my turn"

        # 1) пішаки
        if not self._pawns_ok(board):
            m = self._best_pawn_step(board)
            if m:
                return (m, f"{self.COW_TAG} | pawn-step")
        # 2) коні
        if not self._knights_ok(board):
            m = self._best_knight_step(board)
            if m:
                return (m, f"{self.COW_TAG} | knight-step")
        # 3) слони (перевірка безпеки)
        if not self._bishops_ok(board):
            m = self._best_bishop_step(board)
            if m:
                return (m, f"{self.COW_TAG} | bishop-step(safe)")

        return None, f"{self.COW_TAG} | complete"

    def is_complete(self, board: chess.Board) -> bool:
        return self._pawns_ok(board) and self._knights_ok(board) and self._bishops_ok(board)

    # ---- helpers ----
    def _pawns_ok(self, board: chess.Board) -> bool:
        return self._count_on(board, self.pawn_targets, chess.PAWN) >= 2

    def _knights_ok(self, board: chess.Board) -> bool:
        return self._count_on(board, self.knight_targets, chess.KNIGHT) >= 2

    def _bishops_ok(self, board: chess.Board) -> bool:
        for sq, p in board.piece_map().items():
            if p.color == self.color and p.piece_type == chess.BISHOP:
                if chess.square_rank(sq) != (0 if self.color else 7):
                    return True
        return False

    def _best_pawn_step(self, board: chess.Board) -> Optional[chess.Move]:
        best, score = None, -10**9
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color or p.piece_type != chess.PAWN:
                continue
            s = 0
            if self.pawn_starts.get(m.from_square) == m.to_square:
                s += 900
            elif m.to_square in self.pawn_targets:
                s += 600
            if self._dest_unsafe(board, m):
                s -= 400
            if s > score:
                best, score = m, s
        return best

    def _best_knight_step(self, board: chess.Board) -> Optional[chess.Move]:
        best, score = None, -10**9
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color or p.piece_type != chess.KNIGHT:
                continue
            s = 0
            if m.to_square in self.knight_targets:
                s += 800
            wps = self.knight_waypoints.get(m.from_square, [])
            if m.to_square in wps:
                s += 500 if wps.index(m.to_square) == 0 else 350
            if self._dest_unsafe(board, m):
                s -= 300
            if s > score:
                best, score = m, s
        return best

    def _best_bishop_step(self, board: chess.Board) -> Optional[chess.Move]:
        best, score = None, -10**9
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color or p.piece_type != chess.BISHOP:
                continue
            if self._dest_unsafe(board, m):
                continue
            if self._bishop_move_leaves_pawn_hanging(board, m):
                continue
            s = 0
            if m.to_square in self.bishop_targets:
                s += 420
            if chess.square_rank(m.from_square) == (0 if self.color else 7):
                s += 80
            if s > score:
                best, score = m, s
        return best

    # ---- misc helpers ----
    def _count_on(self, board: chess.Board, squares: Set[int], ptype: int) -> int:
        c = 0
        for sq in squares:
            p = board.piece_at(sq)
            if p and p.color == self.color and p.piece_type == ptype:
                c += 1
        return c

    def _dest_unsafe(self, board: chess.Board, m: chess.Move) -> bool:
        tmp = board.copy(stack=False); tmp.push(m)
        att = len(tmp.attackers(not self.color, m.to_square))
        defn = len(tmp.attackers(self.color, m.to_square))
        return att > 0 and defn == 0

    def _bishop_move_leaves_pawn_hanging(self, board: chess.Board, m: chess.Move) -> bool:
        from_sq = m.from_square
        defended_pawns_before = self._our_pawns_defended_from(board, from_sq)
        if not defended_pawns_before:
            return False
        tmp = board.copy(stack=False); tmp.push(m)
        for psq in defended_pawns_before:
            defenders = len(tmp.attackers(self.color, psq))
            attackers = len(tmp.attackers(not self.color, psq))
            if attackers > 0 and defenders == 0:
                return True
        return False

    def _our_pawns_defended_from(self, board: chess.Board, bishop_sq: int) -> List[int]:
        res = []
        for sq in board.attacks(bishop_sq):
            p = board.piece_at(sq)
            if p and p.color == self.color and p.piece_type == chess.PAWN:
                if bishop_sq in board.attackers(self.color, sq):
                    res.append(sq)
        return res

# ---------- Спільні утиліти ----------
CENTER_16 = {
    chess.C3, chess.D3, chess.E3, chess.F3,
    chess.C4, chess.D4, chess.E4, chess.F4,
    chess.C5, chess.D5, chess.E5, chess.F5,
    chess.C6, chess.D6, chess.E6, chess.F6,
}
def _chebyshev(a: int, b: int) -> int:
    af, ar = chess.square_file(a), chess.square_rank(a)
    bf, br = chess.square_file(b), chess.square_rank(b)
    return max(abs(af - bf), abs(ar - br))

# ---------- Aggressive ----------
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
            if features.get("is_safe_check"): base += 5
            return base
        if features.get("is_capture"):
            return self.weights["capture_defended"]
        if features.get("develops_piece"):
            return self.weights["develop"]
        return self.weights["nothing"]

class _FeatureExtractor:
    @staticmethod
    def _is_hanging_target(board: chess.Board, move: chess.Move, mover_color: bool) -> bool:
        if not board.is_capture(move): return False
        opp = not mover_color
        defenders = board.attackers(opp, move.to_square)
        return len(defenders) == 0
    @staticmethod
    def _is_safe_check(board: chess.Board, move: chess.Move, mover_color: bool) -> bool:
        temp = board.copy(stack=False); temp.push(move)
        if not temp.is_check(): return False
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
    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = True,
    ):
        best_s = -10**9
        best: List[Tuple[chess.Move, Dict[str, Any]]] = []
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color: continue
            feats = self.fx.extract(board, m, self.color)
            s = self.scorer.score(feats)
            if s > best_s: best_s, best = s, [(m, feats)]
            elif s == best_s: best.append((m, feats))
        if not best: return None, "AGGRESSIVE | no legal moves"
        move, feats = random.choice(best)
        return move, f"AGGRESSIVE | score={best_s} feats={ {k:v for k,v in feats.items() if v} }"

# ---------- Fortify (найзахищеніша клітина + develop/capture/пішаки) ----------
class FortifyBot:
    PIECE_DEV_WEIGHTS = {
        chess.KNIGHT: 1.0,
        chess.BISHOP: 0.9,
        chess.ROOK:   0.6,
        chess.QUEEN:  0.5,
        chess.PAWN:   0.4,
        chess.KING:   0.0,
    }
    def __init__(self, color: bool, *, safe_only: bool = False,
                 weights: Optional[Dict[str, float]] = None,
                 tiebreak_jitter: float = 0.01):
        self.color = color
        self.safe_only = safe_only
        self.tiebreak_jitter = tiebreak_jitter
        self.W = {
            "defense_density": 5.0,
            "defenders": 0.5,
            "develop": 3.0,
            "capture": 2.5,
            "opp_doubled_delta": 4.0,
            "opp_shield_delta": 5.0,
        }
        if weights: self.W.update(weights)

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = True,
    ) -> Tuple[Optional[chess.Move], str]:
        m, info = self._best(board)
        if debug and m is not None:
            reason = (
                f"FORTIFY | {board.san(m)} | dens={info['defense_density']} "
                f"def={info['defenders']} att={info['attackers']} | "
                f"dev={int(info['develop'])} cap={int(info['is_capture'])} | "
                f"doubledΔ={info['opp_doubled_delta']} shieldΔ={info['opp_shield_delta']} | "
                f"by={info.get('piece_type')}"
            )
            return m, reason
        return m, "FORTIFY"

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
            if self.safe_only and attackers > 0: continue
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
            # м'який випадковий тай-брейк, щоб не «залипати» в однакових оцінках
            if self.tiebreak_jitter:
                score += random.uniform(-self.tiebreak_jitter, self.tiebreak_jitter)
            if score > best_score:
                best_score = score; best = m
                best_info = {
                    "defense_density": dens, "defenders": defenders, "attackers": attackers,
                    "develop": develops, "is_capture": is_capture,
                    "opp_doubled_delta": max(0, after_doubled - before_doubled),
                    "opp_shield_delta": max(0, before_shield - after_shield),
                    "piece_type": p.piece_type
                }
        return best, best_info

    def _develops(self, board: chess.Board, m: chess.Move, p: chess.Piece) -> bool:
        rank_from = chess.square_rank(m.from_square)
        back_rank = (0 if self.color else 7)
        in_center = m.to_square in CENTER_16
        if p.piece_type in (chess.KNIGHT, chess.BISHOP):
            return (rank_from == back_rank) and in_center
        if p.piece_type == chess.ROOK:
            return (rank_from == back_rank)
        if p.piece_type == chess.QUEEN:
            return (rank_from == back_rank) and (_chebyshev(m.from_square, m.to_square) <= 2)
        if p.piece_type == chess.PAWN:
            # ЛИШЕ центральні пішаки d/e зі стартового ряду
            start_rank = 1 if self.color else 6
            file_from = chess.square_file(m.from_square)
            return (rank_from == start_rank) and (file_from in (3, 4))
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

# ---------- Тактичні утиліти ----------
def creates_hanging_threat(board: chess.Board, move: chess.Move, color: bool) -> bool:
    """Після нашого ходу починаємо атакувати ворожу фігуру без захисту?"""
    tmp = board.copy(stack=False); tmp.push(move)
    enemy = not color
    for t in tmp.attacks(move.to_square):
        p = tmp.piece_at(t)
        if p and p.color == enemy:
            defenders = tmp.attackers(enemy, t)
            if len(defenders) == 0:
                return True
    return False

# ---------- ThreatScout: depth=2 ----------
class ThreatScout:
    W = {
        "pawn_attacks_queen": 120,
        "attack_queen":       90,
        "knight_fork":        70,
        "capture_hanging":    80,
        "capture":            30,
        "check":              50,
        "develop":            15,
        "safety_penalty":     40,
        "safe_bonus":         10,
    }
    VALUABLE = {chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT}

    def __init__(self, color: bool):
        self.color = color

    def probe_depth2(self, board: chess.Board, *, max_opp: int = 18, max_our: int = 24) -> Tuple[Optional[chess.Move], Dict[str, Any]]:
        if board.turn != self.color:
            return None, {"why": "not my turn"}
        best_m1: Optional[chess.Move] = None
        best_score = float("-inf")
        best_info: Dict[str, Any] = {}

        for m1 in board.legal_moves:
            if board.piece_at(m1.from_square) is None:
                continue
            tmp1 = board.copy(stack=False); tmp1.push(m1)
            opp_moves = self._ordered_opp_moves(tmp1)
            if len(opp_moves) > max_opp: opp_moves = opp_moves[:max_opp]

            worst_reply_score = float("inf")
            worst_reply_line: Dict[str, Any] = {}
            for r in opp_moves:
                tmp2 = tmp1.copy(stack=False); tmp2.push(r)
                m2, s2, tag = self._best_our_followup(tmp2, max_our=max_our)
                if s2 < worst_reply_score:
                    worst_reply_score = s2
                    worst_reply_line = {"m2": m2, "tag": tag, "reply": r}

            if worst_reply_score > best_score:
                best_score = worst_reply_score
                best_m1 = m1
                best_info = {"min_score_after_reply": best_score, "line": worst_reply_line}

        if best_m1 is not None and best_score >= 90:
            return best_m1, best_info
        return None, {"why": "no strong depth-2 threat", "best": best_m1, "score": best_score}

    def _ordered_opp_moves(self, board_after_m1: chess.Board) -> List[chess.Move]:
        moves = list(board_after_m1.legal_moves)
        enemy = board_after_m1.turn
        queen_sq = self._find_queen(board_after_m1, enemy)

        def key(m: chess.Move) -> Tuple[int, int, int]:
            tmp = board_after_m1.copy(stack=False); tmp.push(m)
            is_check = int(tmp.is_check())
            is_cap = int(board_after_m1.is_capture(m))
            protects_queen = 0
            if queen_sq is not None:
                before = len(board_after_m1.attackers(enemy, queen_sq))
                after = len(tmp.attackers(enemy, queen_sq))
                protects_queen = int(after > before)
            return (is_check, is_cap, protects_queen)

        moves.sort(key=key, reverse=True)
        return moves

    def _best_our_followup(self, board_after_reply: chess.Board, *, max_our: int) -> Tuple[Optional[chess.Move], int, str]:
        our_moves = list(board_after_reply.legal_moves)
        def our_key(m: chess.Move) -> Tuple[int, int, int]:
            tmp = board_after_reply.copy(stack=False); tmp.push(m)
            return (int(tmp.is_check()), int(board_after_reply.is_capture(m)),
                    int(1 if (board_after_reply.piece_at(m.from_square) and board_after_reply.piece_at(m.from_square).piece_type == chess.PAWN) else 0))
        our_moves.sort(key=our_key, reverse=True)
        if len(our_moves) > max_our: our_moves = our_moves[:max_our]

        best_m2, best_score, best_tag = None, -10**9, ""
        for m2 in our_moves:
            score, tag = self._threat_score(board_after_reply, m2)
            if score > best_score:
                best_m2, best_score, best_tag = m2, score, tag
        return best_m2, best_score, best_tag

    def _threat_score(self, board_before_m2: chess.Board, m2: chess.Move) -> Tuple[int, str]:
        color = self.color
        enemy = not color
        p = board_before_m2.piece_at(m2.from_square)
        if not p: return -10**9, "no-piece"

        tmp = board_before_m2.copy(stack=False); tmp.push(m2)
        to_sq = m2.to_square

        score = 0
        tags: List[str] = []

        queen_sq = self._find_queen(tmp, enemy)
        if p.piece_type == chess.PAWN and queen_sq is not None and queen_sq in tmp.attacks(to_sq):
            score += self.W["pawn_attacks_queen"]; tags.append("pawn->Q")
        if queen_sq is not None and queen_sq in tmp.attacks(to_sq):
            score += self.W["attack_queen"]; tags.append("attackQ")
        if p.piece_type == chess.KNIGHT:
            val_targets = 0
            for t in tmp.attacks(to_sq):
                q = tmp.piece_at(t)
                if q and q.color == enemy and q.piece_type in self.VALUABLE:
                    val_targets += 1
            if val_targets >= 2:
                score += self.W["knight_fork"]; tags.append("N-fork")
        is_cap = board_before_m2.is_capture(m2)
        if is_cap:
            before_piece = board_before_m2.piece_at(m2.to_square)
            if before_piece and before_piece.color == enemy:
                defenders = board_before_m2.attackers(enemy, m2.to_square)
                if len(defenders) == 0:
                    score += self.W["capture_hanging"]; tags.append("cap(hanging)")
                else:
                    score += self.W["capture"]; tags.append("cap")
        if tmp.is_check():
            score += self.W["check"]; tags.append("check")
        if self._mini_develop(board_before_m2, m2, p):
            score += self.W["develop"]; tags.append("dev")
        attackers = len(tmp.attackers(enemy, to_sq))
        defenders = len(tmp.attackers(color, to_sq))
        if attackers > defenders:
            score -= self.W["safety_penalty"] * (attackers - defenders); tags.append("unsafe")
        else:
            score += self.W["safe_bonus"]; tags.append("safe")
        return score, "+".join(tags)

    @staticmethod
    def _find_queen(board: chess.Board, color: bool) -> Optional[int]:
        for sq, piece in board.piece_map().items():
            if piece.color == color and piece.piece_type == chess.QUEEN:
                return sq
        return None

    def _mini_develop(self, board: chess.Board, m: chess.Move, p: chess.Piece) -> bool:
        rank_from = chess.square_rank(m.from_square)
        back_rank = (0 if self.color else 7)
        if p.piece_type in (chess.KNIGHT, chess.BISHOP):
            return rank_from == back_rank and (m.to_square in CENTER_16)
        if p.piece_type == chess.ROOK:
            return rank_from == back_rank
        if p.piece_type == chess.QUEEN:
            return rank_from == back_rank and (_chebyshev(m.from_square, m.to_square) <= 2)
        if p.piece_type == chess.PAWN:
            start_rank = 1 if self.color else 6
            return rank_from == start_rank
        return False

# ---------- Dynamic (комбінатор) ----------
class DynamicBot:
    """
    Порядок стратегій:
      1) SAFE_CHECK → EndgameBot
      2) Якщо НЕТАКТИКИ і COW не завершено → CowOpening
      3) ThreatScout depth-2 → сильна загроза через хід
      4) Fortify (develop або dens≥1)
      5) Aggressive (якщо якийсь хід набрав ≥70)
      6) Endgame (≤7 фігур): мат у 1 / промо / прохідний
      7) Low mobility → Random
      8) Center
    """
    def __init__(self, color: bool):
        self.center   = ChessBot(color)
        self.endgame  = EndgameBot(color)
        self.random   = RandomBot(color)
        self.aggressive = AggressiveBot(color)
        self.fortify  = FortifyBot(color)
        self.cow      = CowOpeningPlanner(color)
        self.scout    = ThreatScout(color)
        self.color = color

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
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

        if board.turn != self.color:
            mv, rs = self.center.choose_move(
                board, context=context, evaluator=evaluator, debug=True
            )
            return (mv, f"CENTER | wait-turn → {rs}") if debug else (mv, "")

        # 1) SAFE CHECK → EndgameBot
        for move in board.legal_moves:
            temp = board.copy(stack=False)
            temp.push(move)
            if temp.is_check():
                defenders = temp.attackers(self.color, move.to_square)
                if defenders:
                    mv, rs = self.endgame.choose_move(
                        board, context=context, evaluator=evaluator, debug=True
                    )
                    return (
                        (mv, f"SAFE_CHECK | delegated to Endgame | {rs}")
                        if debug
                        else (mv, "")
                    )

        # 2) Негайна тактика?
        tactic_available = False
        for m in board.legal_moves:
            if board.is_capture(m):
                tactic_available = True
                break
            tmp = board.copy(stack=False)
            tmp.push(m)
            if tmp.is_check():
                tactic_available = True
                break
            if creates_hanging_threat(board, m, self.color):
                tactic_available = True
                break

        # 2a) Якщо тактики нема і COW не завершено — COW
        if not tactic_available and not self.cow.is_complete(board):
            cmv, creason = self.cow.choose_move(
                board, context=context, evaluator=evaluator, debug=True
            )
            if cmv is not None:
                return (cmv, f"COW | {creason}") if debug else (cmv, "")

        # 3) Пошук сильної ЗАГРОЗИ через хід (depth=2)
        m1, info = self.scout.probe_depth2(board)
        if m1 is not None:
            if debug:
                note = (
                    f"DEPTH2 | minScore={info.get('min_score_after_reply')} "
                    f"line={info.get('line')}"
                )
                return m1, note
            return m1, ""

        # 4) Fortify
        f_move, f_info = self.fortify._best(board)
        if f_move is not None:
            dens = f_info.get("defense_density", 0)
            develops = bool(f_info.get("develop", False))
            if develops or dens >= 1:
                mv, rs = self.fortify.choose_move(
                    board, context=context, evaluator=evaluator, debug=True
                )
                return (f_move, f"FORTIFY | {rs}") if debug else (f_move, "")

        # 5) Aggressive
        fx = _FeatureExtractor()
        sc = Scorer()
        best_aggr = 0
        for m in board.legal_moves:
            feats = fx.extract(board, m, self.color)
            best_aggr = max(best_aggr, sc.score(feats))
        if best_aggr >= 70:
            mv, rs = self.aggressive.choose_move(
                board, context=context, evaluator=evaluator, debug=True
            )
            return (mv, f"AGGRESSIVE | best={best_aggr} | {rs}") if debug else (mv, "")

        # 6) Endgame з пріоритетами
        own_pieces = sum(1 for p in board.piece_map().values() if p.color == self.color)
        if own_pieces <= 7:
            m_mate = self._find_immediate_mate(board)
            if m_mate:
                return (m_mate, "ENDGAME | mate-in-1") if debug else (m_mate, "")
            m_prom = self._find_promotion_push(board)
            if m_prom:
                return (m_prom, "ENDGAME | promotion") if debug else (m_prom, "")
            m_pass = self._find_safe_passed_pawn_push(board)
            if m_pass:
                return (m_pass, "ENDGAME | passed-pawn") if debug else (m_pass, "")
            mv, rs = self.endgame.choose_move(
                board, context=context, evaluator=evaluator, debug=True
            )
            return (mv, f"ENDGAME | {own_pieces} pcs | {rs}") if debug else (mv, "")

        # 7) Low mobility
        mobility = sum(1 for _ in board.legal_moves)
        if mobility < 8:
            mv, rs = self.random.choose_move(
                board, context=context, evaluator=evaluator, debug=True
            )
            return (mv, f"LOW | mobility={mobility} → {rs}") if debug else (mv, "")

        # 8) Center
        mv, rs = self.center.choose_move(
            board, context=context, evaluator=evaluator, debug=True
        )
        return (mv, f"CENTER | {rs}") if debug else (mv, "")

    # ---- пріоритети ендшпілю ----
    def _find_immediate_mate(self, board: chess.Board) -> Optional[chess.Move]:
        for m in board.legal_moves:
            tmp = board.copy(stack=False); tmp.push(m)
            if tmp.is_checkmate():
                return m
        return None

    def _find_promotion_push(self, board: chess.Board) -> Optional[chess.Move]:
        best, dens = None, -10**9
        for m in board.legal_moves:
            if m.promotion:
                tmp = board.copy(stack=False); tmp.push(m)
                d = len(tmp.attackers(self.color, m.to_square)) - len(tmp.attackers(not self.color, m.to_square))
                pref = 2 if m.promotion == chess.QUEEN else 0
                score = d + pref
                if score > dens:
                    best, dens = m, score
        return best

    def _find_safe_passed_pawn_push(self, board: chess.Board) -> Optional[chess.Move]:
        def is_passed(tmpb: chess.Board, sq: int, color: bool) -> bool:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            step = 1 if color == chess.WHITE else -1
            for df in (-1, 0, 1):
                nf = f + df
                if not (0 <= nf <= 7): continue
                rr = r + step
                while 0 <= rr <= 7:
                    s = chess.square(nf, rr)
                    q = tmpb.piece_at(s)
                    if q:
                        if q.color != color and q.piece_type == chess.PAWN:
                            return False
                        break
                    rr += step
            return True

        best, dens = None, -10**9
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color or p.piece_type != chess.PAWN:
                continue
            tmp = board.copy(stack=False); tmp.push(m)
            if is_passed(tmp, m.to_square, self.color):
                d = len(tmp.attackers(self.color, m.to_square)) - len(tmp.attackers(not self.color, m.to_square))
                if d >= 0 and d > dens:
                    best, dens = m, d
        return best

# ---------- Фасади під старий в’ювер (повертають лише chess.Move) ----------
def _just_move(ret):
    if isinstance(ret, tuple) and len(ret) >= 1: return ret[0]
    return ret

class BotAgent:
    """Відповідає «CenterBot (новий)» у вашому UI — центр-стратегія."""
    def __init__(self, color: bool, **kwargs):
        self.impl = ChessBot(color)
    def choose_move(self, board: chess.Board):
        return _just_move(self.impl.choose_move(board, debug=False))

class BotAgentLegacy:
    """Легасі-бот, якщо є; інакше — ChessBot."""
    def __init__(self, color: bool = chess.WHITE, **kwargs):
        try:
            from .legacy_bot import LegacyBot  # type: ignore
            self.impl = LegacyBot(color)
        except Exception:
            self.impl = ChessBot(color)
    def choose_move(self, board: chess.Board):
        return _just_move(self.impl.choose_move(board, debug=False))

class BotAgentRandom:
    """RandomBot у UI."""
    def __init__(self, color: bool, **kwargs):
        self.impl = RandomBot(color)
    def choose_move(self, board: chess.Board):
        return _just_move(self.impl.choose_move(board, debug=False))

class BotAgentEndgame:
    """EndgameBot у UI."""
    def __init__(self, color: bool, **kwargs):
        self.impl = EndgameBot(color)
    def choose_move(self, board: chess.Board):
        return _just_move(self.impl.choose_move(board, debug=False))

class BotAgentDynamic:
    """DynamicBot у UI (містить Cow/ThreatScout/Fortify/Aggressive…)."""
    def __init__(self, color: bool, **kwargs):
        self.impl = DynamicBot(color)
    def choose_move(self, board: chess.Board):
        mv, _reason = self.impl.choose_move(board, debug=True)
        return mv

# ---------- Хелпери/фабрика для випадашки і арени ----------
class _MoveOnlyAdapter:
    """
    Обгортає будь-якого бота з choose_move(...)->(move,reason) у інтерфейс, що повертає ТІЛЬКИ move.
    ДОДАНО: збереження останнього reason для логів арени (get_last_reason()).
    """
    def __init__(self, impl):
        self.impl = impl
        self._last_reason = ""
    def choose_move(self, board: chess.Board):
        try:
            ret = self.impl.choose_move(board, debug=True)
        except TypeError:
            ret = self.impl.choose_move(board)
        if isinstance(ret, tuple):
            move = ret[0]
            self._last_reason = "" if len(ret) < 2 else str(ret[1])
            return move
        else:
            self._last_reason = ""
            return ret
    def get_last_reason(self) -> str:
        return self._last_reason

def _factory(cls) -> Callable[[bool], _MoveOnlyAdapter]:
    return lambda color: _MoveOnlyAdapter(cls(color))

AGENT_FACTORY_BY_EXPORT: Dict[str, Callable[[bool], object]] = {
    "BotAgent":          lambda color: BotAgent(color),
    "BotAgentLegacy":    lambda color: BotAgentLegacy(color),
    "BotAgentRandom":    lambda color: BotAgentRandom(color),
    "BotAgentEndgame":   lambda color: BotAgentEndgame(color),
    "BotAgentDynamic":   lambda color: BotAgentDynamic(color),
    "DynamicBot":        _factory(DynamicBot),
    "FortifyBot":        _factory(FortifyBot),
    "AggressiveBot":     _factory(AggressiveBot),
    "ChessBot":          _factory(ChessBot),
    "EndgameBot":        _factory(EndgameBot),
    "RandomBot":         _factory(RandomBot),
}

def get_agent_names() -> List[str]:
    """Список назв для випадашок (рівно як у __all__)."""
    return list(__all__)

def make_agent(name: str, color: bool):
    """Створити бота за ім’ям із __all__. Якщо нема — повернути DynamicBot (обгорнутий)."""
    factory = AGENT_FACTORY_BY_EXPORT.get(name)
    if factory is None:
        return _MoveOnlyAdapter(DynamicBot(color))
    return factory(color)
