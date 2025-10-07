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

import logging
logger = logging.getLogger(__name__)

from .utility_bot import piece_value
from .threat_map import ThreatMap
from .see import static_exchange_eval
from core.evaluator import Evaluator, escape_squares, is_piece_mated
from core.constants import KING_SAFETY_THRESHOLD
from utils import GameContext


_SHARED_EVALUATOR: Evaluator | None = None


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
            "self_shield_delta": 4.0,  # зміни нашого щитка: + за посилення, - за ослаблення
            "king_safety_delta": 3.0,  # покращення безпеки нашого короля за спрощеним скорером
            "king_defenders_delta": 1.0,  # зміна кількості захисників клітини короля
            "opp_thin_delta": 2.0,    # збільшення кількості "тонких" фігур у опонента
            "self_thin_delta": -2.0,  # штраф за появу нових "тонких" наших фігур
            "opp_escape_delta": 1.0,  # зменшення кількості втеч опонента
            "opp_mated_delta": 5.0,   # зростання кількості атакованих фігур без втечі
            "opp_backward_delta": 3.0, # збільшення кількості відсталих (backward) пішаків опонента
            "self_backward_delta": -3.0, # штраф за збільшення наших відсталих пішаків
        }
        if weights:
            self.W.update(weights)

    # -------------------- ПУБЛІЧНИЙ ІНТЕРФЕЙС --------------------
    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = True,
        king_safety_threshold: int = KING_SAFETY_THRESHOLD,
    ) -> Tuple[Optional[chess.Move], float]:
        """Return the move with the highest defensive score.

        Parameters
        ----------
        board: chess.Board
            Position to analyse.
        context: GameContext | None, optional
            Shared game context (unused).
        evaluator: Evaluator | None, optional
            Reusable evaluator.  A shared one is created if ``None``.
        debug: bool, optional
            Whether to print debugging information.

        Returns
        -------
        tuple[Optional[chess.Move], float]
            Chosen move and its fortification score.
        """

        if context and context.king_safety >= king_safety_threshold:
            if debug:
                msg = (
                    f"FortifyBot: king safety {context.king_safety} ≥ {king_safety_threshold} – skipping fortification"
                )
                logger.debug(msg)
                print(msg)
            return None, 0.0
        elif debug and context:
            msg = (
                f"FortifyBot: king safety {context.king_safety} < {king_safety_threshold} – evaluating moves"
            )
            logger.debug(msg)
            print(msg)

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        if board.turn != self.color:
            return None, 0.0

        moves = list(board.legal_moves)
        if not moves:
            return None, 0.0

        # Базові показники до ходу (для delta-метрик)
        opp = not self.color
        before_doubled_opp = self._count_doubled_pawns(board, opp)
        before_opp_shield = self._king_pawn_shield_count(board, opp)
        before_self_shield = self._king_pawn_shield_count(board, self.color)
        before_king_safety = Evaluator.king_safety(board, self.color)
        before_king_defenders = self._king_defenders_count(board, self.color)
        before_threat_self = ThreatMap(self.color).summary(board)
        before_threat_opp = ThreatMap(opp).summary(board)
        before_thin_self = len(before_threat_self["thin_pieces"])
        before_thin_opp = len(before_threat_opp["thin_pieces"])
        before_opp_escape = self._total_escape_squares(board, opp)
        before_opp_mated = self._count_mated_pieces(board, opp)
        before_backward_self = self._count_backward_pawns(board, self.color)
        before_backward_opp = self._count_backward_pawns(board, opp)

        best = None
        best_score = float("-inf")
        best_info: Dict[str, Any] = {}

        for m in moves:
            score, info = self._score_move(
                board,
                m,
                before_doubled_opp,
                before_opp_shield,
                before_thin_opp,
                before_thin_self,
                before_opp_escape,
                before_opp_mated,
                before_self_shield,
                before_king_safety,
                before_king_defenders,
                before_backward_self,
                before_backward_opp,
                evaluator,
            )
            if score > best_score:
                best, best_score, best_info = m, score, info

        if debug and best is not None:
            # Retain a verbose string for potential manual debugging.
            details = (
                f"dens={best_info['defense_density']} def={best_info['defenders']} att={best_info['attackers']} | "
                f"dev={int(best_info['develop'])} cap={int(best_info['is_capture'])} "
                f"gain={best_info['capture_gain']} see={best_info['see_gain']} "
                f"thinΔ={best_info['opp_thin_delta']} selfThinΔ={best_info['self_thin_delta']} "
                f"doubledΔ={best_info['opp_doubled_delta']} "
                f"oppShieldΔ={best_info['opp_shield_delta']} selfShieldΔ={best_info['self_shield_delta']} "
                f"kSafeΔ={best_info['king_safety_delta']} kDefΔ={best_info['king_defenders_delta']} "
                f"oppBackΔ={best_info['opp_backward_delta']} selfBackΔ={best_info['self_backward_delta']} "
                f"escΔ={best_info['opp_escape_delta']} mateΔ={best_info['opp_mated_delta']} "
                f"score={round(best_score,2)}"
            )
            # Debug branch still returns numerical confidence as second value
            # but prints details for easier tracing.
            msg = f"FortifyBot: {details}"
            logger.debug(msg)
            print(msg)

        return best, float(best_score if best is not None else 0.0)

    # -------------------- ОЦІНКА ХОДУ --------------------
    def _score_move(
        self,
        board: chess.Board,
        m: chess.Move,
        before_doubled_opp: int,
        before_opp_shield: int,
        before_thin_opp: int,
        before_thin_self: int,
        before_opp_escape: int,
        before_opp_mated: int,
        before_self_shield: int,
        before_king_safety: int,
        before_king_defenders: int,
        before_backward_self: int,
        before_backward_opp: int,
        evaluator: Evaluator,
    ) -> Tuple[float, Dict[str, Any]]:
        """Return the defensive score of ``m`` using ``evaluator``.

        The ``evaluator`` instance is reused across moves to avoid
        repeatedly constructing :class:`Evaluator` objects.
        """
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
                "self_thin_delta": 0,
                "opp_escape_delta": 0,
                "opp_mated_delta": 0,
            }

        # Develop евристика
        develops = self._develops(board, m)

        # Δ здвоєних пішаків у опонента
        after_doubled_opp = self._count_doubled_pawns(tmp, not self.color)
        opp_doubled_delta = max(0, after_doubled_opp - before_doubled_opp)

        # Δ «щитка» пішаків перед королем опонента
        after_opp_shield = self._king_pawn_shield_count(tmp, not self.color)
        opp_shield_delta = max(0, before_opp_shield - after_opp_shield)

        # Зміна нашого щитка (може бути від'ємною або додатною)
        after_self_shield = self._king_pawn_shield_count(tmp, self.color)
        self_shield_delta = after_self_shield - before_self_shield

        # Δ безпеки нашого короля та кількості його захисників
        after_king_safety = Evaluator.king_safety(tmp, self.color)
        king_safety_delta = after_king_safety - before_king_safety
        after_king_defenders = self._king_defenders_count(tmp, self.color)
        king_defenders_delta = after_king_defenders - before_king_defenders

        # Δ "тонких" фігур опонента і наших власних
        after_threat_self = ThreatMap(self.color).summary(tmp)
        after_threat_opp = ThreatMap(not self.color).summary(tmp)
        after_thin_self = len(after_threat_self["thin_pieces"])
        after_thin_opp = len(after_threat_opp["thin_pieces"])
        opp_thin_delta = max(0, after_thin_opp - before_thin_opp)
        self_thin_delta = max(0, after_thin_self - before_thin_self)

        # Δ втеч опонента
        after_opp_escape = self._total_escape_squares(tmp, not self.color)
        opp_escape_delta = max(0, before_opp_escape - after_opp_escape)

        # Δ атакованих беззахисних фігур опонента
        after_opp_mated = self._count_mated_pieces(tmp, not self.color)
        opp_mated_delta = max(0, after_opp_mated - before_opp_mated)

        # Δ відсталих пішаків (backward)
        after_backward_self = self._count_backward_pawns(tmp, self.color)
        after_backward_opp = self._count_backward_pawns(tmp, not self.color)
        self_backward_delta = after_backward_self - before_backward_self
        opp_backward_delta = after_backward_opp - before_backward_opp

        score = (
            self.W["defense_density"] * defense_density +
            self.W["defenders"] * defenders +
            self.W["develop"] * (1 if develops else 0) +
            self.W["capture"] * gain +
            self.W["opp_doubled_delta"] * opp_doubled_delta +
            self.W["opp_shield_delta"] * opp_shield_delta +
            self.W["self_shield_delta"] * self_shield_delta +
            self.W["king_safety_delta"] * king_safety_delta +
            self.W["king_defenders_delta"] * king_defenders_delta +
            self.W["opp_thin_delta"] * opp_thin_delta +
            self.W["self_thin_delta"] * self_thin_delta +
            self.W["opp_escape_delta"] * opp_escape_delta +
            self.W["opp_mated_delta"] * opp_mated_delta +
            self.W["opp_backward_delta"] * opp_backward_delta +
            self.W["self_backward_delta"] * self_backward_delta +
            see_gain
        )

        score += evaluator.position_score(tmp, self.color)

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
            "self_shield_delta": self_shield_delta,
            "king_safety_delta": king_safety_delta,
            "king_defenders_delta": king_defenders_delta,
            "opp_thin_delta": opp_thin_delta,
            "self_thin_delta": self_thin_delta,
            "opp_escape_delta": opp_escape_delta,
            "opp_mated_delta": opp_mated_delta,
            "opp_backward_delta": opp_backward_delta,
            "self_backward_delta": self_backward_delta,
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

    def _total_escape_squares(self, board: chess.Board, color: bool) -> int:
        """Total number of safe moves for all pieces of ``color``."""
        total = 0
        for sq, piece in board.piece_map().items():
            if piece.color == color:
                total += len(escape_squares(board, sq))
        return total

    def _count_mated_pieces(self, board: chess.Board, color: bool) -> int:
        """Return number of pieces of ``color`` that are currently mated."""
        total = 0
        for sq, piece in board.piece_map().items():
            if piece.color == color and is_piece_mated(board, sq):
                total += 1
        return total

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

    def _king_defenders_count(self, board: chess.Board, color: bool) -> int:
        """Кількість наших фігур, що захищають клітину короля."""
        ksq = board.king(color)
        if ksq is None:
            return 0
        return len(board.attackers(color, ksq))

    def _count_backward_pawns(self, board: chess.Board, color: bool) -> int:
        """Груба евристика для підрахунку відсталих (backward) пішаків.

        Вважаємо пішака відсталим, якщо:
        - на суміжних файлах немає дружнього пішака на тій самій або позаду
          (для білих: на рядках <= його; для чорних: на рядках >= його), який міг би
          потенційно підтримати просування;
        - клітина попереду (на один ряд) атакована пішаками супротивника.
        """
        total = 0
        enemy = not color
        for sq, piece in board.piece_map().items():
            if piece.color != color or piece.piece_type != chess.PAWN:
                continue

            f = chess.square_file(sq)
            r = chess.square_rank(sq)

            # Клітина попереду
            fr = r + (1 if color == chess.WHITE else -1)
            if not (0 <= fr < 8):
                continue
            forward_sq = chess.square(f, fr)

            # Чи атакована пішаками супротивника?
            attacked_by_enemy_pawn = False
            for att in board.attackers(enemy, forward_sq):
                ap = board.piece_at(att)
                if ap and ap.color == enemy and ap.piece_type == chess.PAWN:
                    attacked_by_enemy_pawn = True
                    break
            if not attacked_by_enemy_pawn:
                continue

            # Чи є дружній пішак на суміжних файлах не попереду цього?
            has_supporting_pawn = False
            for af in (f - 1, f + 1):
                if 0 <= af < 8:
                    if color == chess.WHITE:
                        ranks_iter = range(r, -1, -1)
                    else:
                        ranks_iter = range(r, 8)
                    for rr in ranks_iter:
                        adj_sq = chess.square(af, rr)
                        p2 = board.piece_at(adj_sq)
                        if p2 and p2.color == color and p2.piece_type == chess.PAWN:
                            has_supporting_pawn = True
                            break
                    if has_supporting_pawn:
                        break

            if not has_supporting_pawn:
                total += 1

        return total
