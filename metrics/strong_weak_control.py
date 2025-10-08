from __future__ import annotations

from typing import Dict, Tuple

import chess

from .attack_map import attack_count_per_square


def control_balance(board: chess.Board) -> Dict[bool, Tuple[int, ...]]:
    """Return per-square control balance for both colours.

    For each square ``s`` this computes ``attackers(color, s) - attackers(!color, s)``.
    Positive values mean the colour more strongly controls that square.
    """
    counts = attack_count_per_square(board)
    white = counts[chess.WHITE]
    black = counts[chess.BLACK]
    white_bal = tuple(white[i] - black[i] for i in range(64))
    black_bal = tuple(black[i] - white[i] for i in range(64))
    return {chess.WHITE: white_bal, chess.BLACK: black_bal}


__all__ = ["control_balance"]
