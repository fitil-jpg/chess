# fortify_bot.py
# Призначення: Бот, що обирає хід на «найбільш захищену клітину» (max defense density),
# із пріоритетами: develop > capture/тактичні вигоди > інше.
# Додаткові бонуси:
#   • створення здвоєних пішаків у суперника (delta > 0)
#   • послаблення «щитка» пішаків перед королем суперника (delta > 0)
#
# Інтеграція: from .fortify_bot import FortifyBot
# Виклик: move, confidence = FortifyBot(color).choose_move(board)

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any
import chess

from .utility_bot import piece_value
from .threat_map import ThreatMap
from .see import static_exchange_eval


class FortifyBot:
    def __init__(self, color: bool, *, safe_only: bool = False, weights: Optional[Dict[str, float]] = None):
        self.color = color
        self.safe_only = safe_only
        # Ваги (тюнінг на ваш смак)
        self.W = {
            "defense_density": 5.0,   # (defenders - attackers) клітини призначення
            "defenders": 0.5,         # невелика добавка за сам факт багатьох захисників
            "develop": 3.0,           # пріоритет розвитку
            "capture": 2.5,           # взяття
            "opp_doubled_delta": 4.0, # збільшення кількості здвоєних пішаків у опонента
            "opp_shield_delta": 5.0,  # зменшення кількості пішаків у «щитку» перед королем опонента
            "opp_thin_delta": 2.0,    # збільшення кількості "тонких" фігур у опонента
        }
        if weights:
            self.W.update(weights)

    # -------------------- ПУБЛІЧНИЙ ІНТЕРФЕЙС --------------------
    def choose_move(self, board: chess.Board, debug: bool = True) -> Tuple[Optional[chess.Move], float]:
        """Return the move with the highest defensive score.

        ``confidence`` corresponds to the internal fortification score based on
        defense density and other heuristics.  When there are no legal moves or
        it's not our turn, ``confidence`` is ``0.0`` and ``move`` is ``None``.
        """

        if board.turn != self.color:
            return None, 0.0

        moves = list(board.legal_moves)
        if not moves:
            return None, 0.0

        # Базові показники до ходу (для delta-метрик)
        opp = not self.color
        before_doubled_opp = self._count_doubled_pawns(board, opp)
        before_opp_shield = self._king_pawn_shield_count(board, opp)
        before_threat_opp = ThreatMap(opp).summary(board)
        before_thin_opp = len(before_threat_opp["thin_pieces"])

        best = None
        best_score = float("-inf")
        best_info: Dict[str, Any] = {}

        for m in moves:
            score, info = self._score_move(
                board, m, before_doubled_opp, before_opp_shield, before_thin_opp
            )
            if score > best_score:
                best, best_score, best_info = m, score, info

        if debug and best is not None:
            # Retain a verbose string for potential manual debugging.
            details = (
                f"dens={best_info['defense_density']} def={best_info['defenders']} att={best_info['attackers']} | "
                f"dev={int(best_info['develop'])} cap={int(best_info['is_capture'])} "
                f"gain={best_info['capture_gain']} see={best_info['see_gain']} "
                f"thinΔ={best_info['opp_thin_delta']} doubledΔ={best_info['opp_doubled_delta']} "
                f"shieldΔ={best_info['opp_shield_delta']} score={round(best_score,2)}"
            )
            # Debug branch still returns numerical confidence as second value
            # but prints details for easier tracing.
            print(f"FortifyBot: {details}")

        return best, float(best_score if best is not None else 0.0)

    # -------------------- ОЦІНКА ХОДУ --------------------
    def _score_move(self, board: chess.Board, m: chess.Move,
                    before_doubled_opp: int, before_opp_shield: int,
                    before_thin_opp: int) -> Tuple[float, Dict[str, Any]]:
        tmp = board.copy(stack=False)
        tmp.push(m)

        to_sq = m.to_square
        defenders = len(tmp.attackers(self.color, to_sq))
        attackers = len(tmp.attackers(not self.color, to_sq))
        defense_density = defenders - attackers

        # Взяття та матеріальні оцінки
        captured = board.piece_at(m.to_square)
        attacker = board.piece_at(m.from_square)
        gain = (piece_value(captured) if captured else 0) - (
            piece_value(attacker) if attacker else 0
        )

        is_capture = board.is_capture(m)
        see_gain = static_exchange_eval(board, m) if is_capture else 0

        if self.safe_only and (attackers > 0 or see_gain < 0):
            return float("-1e9"), {
                "defense_density": defense_density,
                "defenders": defenders,
                "attackers": attackers,
                "develop": False,
                "is_capture": is_capture,
                "capture_gain": gain,
                "see_gain": see_gain,
                "opp_doubled_delta": 0,
                "opp_shield_delta": 0,
                "opp_thin_delta": 0,
            }

        # Develop евристика
        develops = self._develops(board, m)

        # Δ здвоєних пішаків у опонента
        after_doubled_opp = self._count_doubled_pawns(tmp, not self.color)
        opp_doubled_delta = max(0, after_doubled_opp - before_doubled_opp)

        # Δ «щитка» пішаків перед королем опонента
        after_opp_shield = self._king_pawn_shield_count(tmp, not self.color)
        opp_shield_delta = max(0, before_opp_shield - after_opp_shield)

        # Δ "тонких" фігур опонента
        _after_threat_self = ThreatMap(self.color).summary(tmp)
        after_threat_opp = ThreatMap(not self.color).summary(tmp)
        after_thin_opp = len(after_threat_opp["thin_pieces"])
        opp_thin_delta = max(0, after_thin_opp - before_thin_opp)

        score = (
            self.W["defense_density"] * defense_density +
            self.W["defenders"] * defenders +
            self.W["develop"] * (1 if develops else 0) +
            self.W["capture"] * gain +
            self.W["opp_doubled_delta"] * opp_doubled_delta +
            self.W["opp_shield_delta"] * opp_shield_delta +
            self.W["opp_thin_delta"] * opp_thin_delta +
            see_gain
        )

        info = {
            "defense_density": defense_density,
            "defenders": defenders,
            "attackers": attackers,
            "develop": develops,
            "is_capture": is_capture,
            "capture_gain": gain,
            "see_gain": see_gain,
            "opp_doubled_delta": opp_doubled_delta,
            "opp_shield_delta": opp_shield_delta,
            "opp_thin_delta": opp_thin_delta,
        }
        return score, info

    # -------------------- ЕВРИСТИКИ --------------------
    def _develops(self, board: chess.Board, m: chess.Move) -> bool:
        """Проста develop-логіка: вивести легкі фігури з базової лінії в центр, розкрити тури, не ганяти ферзя зарано."""
        p = board.piece_at(m.from_square)
        if not p:
            return False

        # Базова лінія
        rank_from = chess.square_rank(m.from_square)
        is_back_rank = (rank_from == (0 if self.color else 7))

        # Центр 4x4
        center = {
            chess.C3, chess.D3, chess.E3, chess.F3,
            chess.C4, chess.D4, chess.E4, chess.F4,
            chess.C5, chess.D5, chess.E5, chess.F5,
            chess.C6, chess.D6, chess.E6, chess.F6,
        }

        if p.piece_type in (chess.KNIGHT, chess.BISHOP):
            return is_back_rank and (m.to_square in center)

        if p.piece_type == chess.ROOK:
            # Відкриття ліній з базової (інколи коли пішак рушив)
            return is_back_rank

        if p.piece_type == chess.QUEEN:
            # Скромний розвиток ферзя: з back rank і не занадто далеко
            return is_back_rank and (chess.square_distance(m.from_square, m.to_square) <= 2)

        if p.piece_type == chess.KING:
            # Ми не рахуємо рокіровку тут (окремо можна додати)
            return False

        if p.piece_type == chess.PAWN:
            # Перший крок пішаком з 2/7 ряду — умовно теж «розвиток»
            start_rank = 1 if self.color else 6
            return chess.square_rank(m.from_square) == start_rank

        return False

    def _count_doubled_pawns(self, board: chess.Board, color: bool) -> int:
        """Кількість файлів, де у color ≥ 2 пішаків (спрощений показник «здвоєних»)."""
        files = [0]*8
        for sq, piece in board.piece_map().items():
            if piece.color == color and piece.piece_type == chess.PAWN:
                files[chess.square_file(sq)] += 1
        return sum(1 for c in files if c >= 2)

    def _king_pawn_shield_count(self, board: chess.Board, color: bool) -> int:
        """
        Кількість пішаків у «щитку» перед королем color.
        Беремо 3 файли навколо короля (file-1..file+1) і ряд 2 (для білих) або 7 (для чорних),
        а також ще один ряд далі (ряд 3 для білих/6 для чорних) — як простий щиток 2 ряди завглибшки.
        """
        ksq = board.king(color)
        if ksq is None:
            return 0
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
