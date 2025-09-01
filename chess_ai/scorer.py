"""
scorer.py — універсальний скорер для feature map.

Пріоритет (зверху вниз):
capture_hanging > pawn_attacks_queen > attacks_queen >
knight_fork (динамічно через fork_pair_priority) >
bishop_skewer > check > capture > develop > threaten_hanging > nothing

У фіналі все множимо на sigmoid_multiplier(defenders-attackers, k=0.6).
"""

from __future__ import annotations
from typing import Dict, Any
import chess
from core.constants import PIECE_PRIORITY, fork_pair_priority, sigmoid_multiplier

import logging
logger = logging.getLogger(__name__)

class Scorer:
    """
    Легко тюниться через PRIORITY_SCALE та ваги нижче.
    """
    PRIORITY_SCALE = 0.09  # масштаб «цінностей фігур» у бали (~0..150)

    def __init__(self):
        self.weights: Dict[str, int] = {
            "capture_hanging":      140,
            "check":                 85,
            "capture_defended":      40,
            "develop":               35,
            "threaten_hanging":      30,
            "open_file_to_king":      75,
            "active_piece":            5,
            "nothing":                1,
        }
        self.last_check_signature = None
        self.last_check_eval = None
        self.check_repeat_count = 0
        self.repeat_penalty = 20

    def _score_attack_queen(self, pawn: bool) -> int:
        base = PIECE_PRIORITY[chess.QUEEN]
        if pawn:
            base = int(base * 1.15)  # пішаком давити на Q цінніше
        return int(base * self.PRIORITY_SCALE)

    def _score_knight_fork(self, pairs: list[str]) -> int:
        if not pairs:
            return 0
        raw = fork_pair_priority(pairs[0])  # уже враховано (def/unprot)
        return int(raw * self.PRIORITY_SCALE)

    def score(self, f: Dict[str, Any]) -> int:
        # 1) базовий бал за фічі
        if f.get("capture_hanging"):
            base = self.weights["capture_hanging"]
        elif f.get("pawn_attacks_queen"):
            base = self._score_attack_queen(pawn=True)
        elif f.get("attacks_queen"):
            base = self._score_attack_queen(pawn=False)
        elif f.get("open_file_to_king"):
            base = self.weights["open_file_to_king"]
        else:
            fork_s = self._score_knight_fork(f.get("knight_next_fork_pairs", []))
            if fork_s:
                base = fork_s
            elif f.get("bishop_next_skewer_qr"):
                base = max(90, int((PIECE_PRIORITY[chess.QUEEN] + PIECE_PRIORITY[chess.ROOK]) * 0.08))
            elif f.get("gives_check"):
                base = self.weights["check"] + (5 if f.get("is_safe_check") else 0)
            elif f.get("is_capture"):
                base = self.weights["capture_defended"]
            elif f.get("develops_piece"):
                base = self.weights["develop"]
            elif f.get("active_piece"):
                base = self.weights["active_piece"] * int(f.get("active_piece"))
            elif f.get("threaten_hanging"):
                base = self.weights["threaten_hanging"]
            else:
                base = self.weights["nothing"]

        if f.get("gives_check"):
            sig = f.get("check_signature")
            eval_score = f.get("eval_score")
            if (
                sig is not None
                and sig == self.last_check_signature
                and eval_score is not None
                and self.last_check_eval is not None
                and eval_score <= self.last_check_eval
            ):
                self.check_repeat_count += 1
            else:
                self.check_repeat_count = 1
            self.last_check_signature = sig
            self.last_check_eval = eval_score
            if self.check_repeat_count >= 3:
                base -= self.repeat_penalty
        else:
            self.check_repeat_count = 0

        # 2) м’який безпековий множник за захищеність клітини після ходу
        dens = int(f.get("safety_balance", 0))
        mult = sigmoid_multiplier(dens, k=0.6, amp=0.5)
        return int(round(base * mult))
