import logging
logger = logging.getLogger(__name__)

import os
import json
from typing import Sequence

import chess

from .phase import GamePhaseDetector

# Path to PST data file (JSON)
PST_FILE = os.path.join(os.path.dirname(__file__), "..", "pst.json")

# Phases and default pieces
PHASES = ["opening", "middlegame", "endgame"]
PIECE_SYMBOLS = ["P", "N", "B", "R", "Q", "K"]


def _empty_piece_table():
    return {sym: [0] * 64 for sym in PIECE_SYMBOLS}


def _empty_phase_table():
    return {phase: _empty_piece_table() for phase in PHASES}


def _ensure_structure(data):
    phases = data.setdefault("phases", _empty_phase_table())
    for phase in PHASES:
        phase_map = phases.setdefault(phase, _empty_piece_table())
        for sym in PIECE_SYMBOLS:
            phase_map.setdefault(sym, [0] * 64)
    steps = data.setdefault("steps", {})
    for tbl in steps.values():
        for sym in PIECE_SYMBOLS:
            tbl.setdefault(sym, [0] * 64)
    return data


def load_pst(path: str = PST_FILE):
    """Load PST from JSON; return empty structure if file missing."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Backward compatibility: old flat format or phase-only
            if "phases" not in data:
                if any(phase in data for phase in PHASES):
                    phases = {phase: data.get(phase, _empty_piece_table()) for phase in PHASES}
                    data = {"phases": phases, "steps": {}}
                else:
                    data = {"phases": _empty_phase_table(), "steps": {}}
            return _ensure_structure(data)
        except Exception:
            pass
    return {"phases": _empty_phase_table(), "steps": {}}


# Global PST loaded at import time
PST = load_pst()


def save_pst(path: str = PST_FILE):
    """Persist current PST to JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(PST, f)


def _apply_board_to_table(board: chess.Board, winner_color: bool, table):
    for sq, piece in board.piece_map().items():
        if piece.color != winner_color:
            continue
        sym = piece.symbol().upper()
        idx = sq if winner_color == chess.WHITE else chess.square_mirror(sq)
        table[sym][idx] += 1


def update_from_board(board: chess.Board, winner_color: bool):
    """Update phase tables from the final board of a decisive game."""
    phase = GamePhaseDetector.detect(board)
    _apply_board_to_table(board, winner_color, PST["phases"][phase])
    save_pst()


def update_from_history(moves: Sequence[chess.Move], winner_color: bool, steps: Sequence[int]):
    """Replay move history and update PST at specified ply numbers."""
    temp = chess.Board()
    for i, mv in enumerate(moves, start=1):
        temp.push(mv)
        if i in steps:
            phase = GamePhaseDetector.detect(temp)
            _apply_board_to_table(temp, winner_color, PST["phases"][phase])
            step_tbl = PST["steps"].setdefault(str(i), _empty_piece_table())
            _apply_board_to_table(temp, winner_color, step_tbl)
    save_pst()