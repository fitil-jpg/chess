"""Detect tactical and structural scenarios on a simple board matrix."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Sequence, Optional

RULES_PATH = Path(__file__).with_name("rules.json")

with open(RULES_PATH, "r", encoding="utf-8") as fh:
    RULES = {rule["id"]: rule for rule in json.load(fh)["rules"]}

FILES = "abcdefgh"


def detect_scenarios(board: Sequence[Sequence[Optional[str]]]) -> List[Dict]:
    """Return detected scenarios for a given board state.

    The ``board`` is expected to be an 8x8 matrix of piece identifiers such as
    ``"white-pawn"`` or ``"black-knight"`` with ``None`` for empty squares.
    Coordinates use ``board[rank][file]`` with ``rank`` 0 being the top (rank 8)
    and ``file`` 0 the ``a``-file.
    """
    scenarios: List[Dict] = []
    scenarios.extend(_detect_isolated_pawns(board))
    scenarios.extend(_detect_knight_forks(board))
    return scenarios


def _square_name(file: int, rank: int) -> str:
    return f"{FILES[file]}{rank}"


def _detect_isolated_pawns(board: Sequence[Sequence[Optional[str]]]) -> List[Dict]:
    results: List[Dict] = []
    for r in range(8):
        for f in range(8):
            piece = board[r][f]
            if piece not in ("white-pawn", "black-pawn"):
                continue
            color = piece.split("-")[0]
            # gather adjacent files
            adj_files = []
            if f > 0:
                adj_files.append(f - 1)
            if f < 7:
                adj_files.append(f + 1)
            isolated = True
            for af in adj_files:
                for rr in range(8):
                    if board[rr][af] == f"{color}-pawn":
                        isolated = False
                        break
                if not isolated:
                    break
            if isolated:
                results.append({
                    "id": "isolated_pawn",
                    "square": _square_name(f, 8 - r),
                    "color": color,
                })
    return results


def _detect_knight_forks(board: Sequence[Sequence[Optional[str]]]) -> List[Dict]:
    results: List[Dict] = []
    moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for r in range(8):
        for f in range(8):
            piece = board[r][f]
            if piece not in ("white-knight", "black-knight"):
                continue
            color = piece.split("-")[0]
            enemy = "black" if color == "white" else "white"
            targets: List[str] = []
            for dr, df in moves:
                rr, ff = r + dr, f + df
                if 0 <= rr < 8 and 0 <= ff < 8:
                    target = board[rr][ff]
                    if target and target.startswith(enemy):
                        targets.append(_square_name(ff, 8 - rr))
            if len(targets) >= 2:
                results.append({
                    "id": "knight_fork",
                    "square": _square_name(f, 8 - r),
                    "targets": targets,
                    "color": color,
                })
    return results
