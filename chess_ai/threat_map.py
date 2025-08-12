# chess_ai/threat_map.py
from __future__ import annotations
from typing import List, Tuple, Dict, Any
import chess

class ThreatMap:
    """
    Сенсор загроз для color:
      summary(board) -> {
        "thin_pieces": List[(sq, our_def, opp_att)]  # від найтонших до менш тонких
        "max_attacked": int|None,                     # клітина з найбільшою кількістю атак суперника
        "max_defended": int|None,                     # клітина з найбільшою кількістю нашого захисту
      }
    thin_threshold=0 означає: показувати фігури з def - att <= 0.
    """
    def __init__(self, color: bool, thin_threshold: int = 0) -> None:
        self.color = color
        self.enemy = not color
        self.thin_threshold = thin_threshold

    def defenders(self, board: chess.Board, sq: int) -> int:
        return len(board.attackers(self.color, sq))

    def attackers(self, board: chess.Board, sq: int) -> int:
        return len(board.attackers(self.enemy, sq))

    def summary(self, board: chess.Board) -> Dict[str, Any]:
        thin: List[Tuple[int, int, int]] = []  # (sq, def, att)
        max_att_sq = None
        max_att_val = -1
        max_def_sq = None
        max_def_val = -1

        # глобальні піки атак/захисту по клітинах
        for sq in chess.SQUARES:
            d = self.defenders(board, sq)
            a = self.attackers(board, sq)
            if a > max_att_val:
                max_att_val, max_att_sq = a, sq
            if d > max_def_val:
                max_def_val, max_def_sq = d, sq

        # «тонкі» наші фігури
        for sq, pc in board.piece_map().items():
            if pc.color != self.color:
                continue
            d = self.defenders(board, sq)
            a = self.attackers(board, sq)
            if (d - a) <= self.thin_threshold:
                thin.append((sq, d, a))

        # найгірші першими: (def-att) зростає, при рівності — більше атак, менше захисту
        thin.sort(key=lambda t: (t[1] - t[2], -t[2], t[1]))
        return {"thin_pieces": thin, "max_attacked": max_att_sq, "max_defended": max_def_sq}
