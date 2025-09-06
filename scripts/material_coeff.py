#!/usr/bin/env python3
"""Utility functions for computing material metrics on a chess board.

The coefficient R is defined as the material difference (white - black)
using the classical piece values.  The module also exposes
``average_strength`` which returns the mean material value of the pieces
remaining for a given colour.

Both helpers are lightweight and intended for quick experiments or
command-line usage.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

# Ensure the vendored ``chess`` package is importable when the script is used as
# a stand-alone command.
VENDOR_PATH = Path(__file__).resolve().parents[1] / "vendors"
if str(VENDOR_PATH) not in sys.path:
    sys.path.append(str(VENDOR_PATH))

import chess


# Classical piece values.  Kings are ignored since they are always present and
# their value would dominate the average strength metric.
PIECE_VALUES: Dict[chess.PieceType, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}


def coefficient_r(board: chess.Board) -> int:
    """Return material difference (white - black) for ``board``."""
    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score


def average_strength(board: chess.Board, color: chess.Color) -> float:
    """Return the average material value of all pieces for ``color``.

    If a side has no material besides the king, the function returns ``0``.
    """
    piece_count = sum(len(board.pieces(pt, color)) for pt in PIECE_VALUES)
    if piece_count == 0:
        return 0.0
    total = sum(
        len(board.pieces(pt, color)) * PIECE_VALUES[pt] for pt in PIECE_VALUES
    )
    return total / piece_count


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: material_coeff.py <FEN>")
        return 1
    board = chess.Board(argv[1])
    print(f"Coefficient R: {coefficient_r(board)}")
    print(
        f"Average strength (white): {average_strength(board, chess.WHITE):.2f}"
    )
    print(
        f"Average strength (black): {average_strength(board, chess.BLACK):.2f}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main(sys.argv))
