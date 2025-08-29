"""Detect tactical and structural scenarios from FEN strings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from fen_handler import fen_to_board_state

RULES_PATH = Path(__file__).with_name("scenario_rules.json")

with open(RULES_PATH, "r", encoding="utf-8") as fh:
    RULES = {rule["id"]: rule for rule in json.load(fh)["rules"]}

FILES = "abcdefgh"


def detect_scenarios(fen: str) -> List[Dict]:
    """Return detected scenarios for a given FEN string.

    Parameters
    ----------
    fen:
        Forsyth-Edwards Notation describing the board position.

    Returns
    -------
    list of dict
        Detected scenarios with metadata such as ``id`` and ``square``.  The
        ``color`` field is populated from :data:`scenario_rules.json` when
        available.
    """

    board = fen_to_board_state(fen)
    scenarios: List[Dict] = []
    scenarios.extend(_detect_isolated_pawns(board))
    scenarios.extend(_detect_knight_forks(board))
    for sc in scenarios:
        rule = RULES.get(sc["id"])
        if rule and "color" in rule:
            sc.setdefault("color", rule["color"])
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
                    "side": color,
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
                    "side": color,
                })
    return results
