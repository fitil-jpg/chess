"""Layered piece-square table (PST) loader utilities."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

import chess

from core.phase import GamePhaseDetector
from pst_tables import PST_MG

# --- Constants ----------------------------------------------------------------

PIECE_TYPES: Sequence[int] = (
    chess.PAWN,
    chess.KNIGHT,
    chess.BISHOP,
    chess.ROOK,
    chess.QUEEN,
    chess.KING,
)

PIECE_SYMBOLS = {
    chess.PAWN: "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK: "R",
    chess.QUEEN: "Q",
    chess.KING: "K",
}

SYMBOL_TO_PIECE = {sym: ptype for ptype, sym in PIECE_SYMBOLS.items()}

PHASES = ("midgame", "endgame")
LAYERS = ("base", "user", "learned")

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"

LAYER_FILENAMES: Dict[str, Dict[str, str]] = {
    "base": {"midgame": "pst_base_mg.json", "endgame": "pst_base_eg.json"},
    "user": {"midgame": "pst_user_mg.json", "endgame": "pst_user_eg.json"},
    "learned": {
        "midgame": "pst_learned_mg.json",
        "endgame": "pst_learned_eg.json",
    },
}

# --- Helpers -------------------------------------------------------------------


def _empty_table() -> List[int]:
    return [0] * 64


def _empty_phase_tables() -> Dict[int, List[int]]:
    return {ptype: _empty_table() for ptype in PIECE_TYPES}


def _ensure_length(values: Sequence[int]) -> List[int]:
    """Return a list of length 64, padding/truncating as required."""
    result = [int(v) for v in list(values)[:64]]
    if len(result) < 64:
        result.extend([0] * (64 - len(result)))
    return result


def _parse_piece_key(key) -> int | None:
    if isinstance(key, int) and key in PIECE_TYPES:
        return key
    if isinstance(key, str):
        key = key.strip()
        if not key:
            return None
        if key.isdigit():
            value = int(key)
            if value in PIECE_TYPES:
                return value
        upper = key.upper()
        if upper in SYMBOL_TO_PIECE:
            return SYMBOL_TO_PIECE[upper]
    return None


def _default_layer(layer: str, phase: str) -> Dict[int, List[int]]:
    if layer == "base" and phase == "midgame":
        return {ptype: list(PST_MG.get(ptype, _empty_table())) for ptype in PIECE_TYPES}
    if layer == "base" and phase == "endgame":
        # Fall back to middlegame defaults when dedicated endgame tables are absent.
        return {ptype: list(PST_MG.get(ptype, _empty_table())) for ptype in PIECE_TYPES}
    return _empty_phase_tables()


def _load_json_table(path: Path) -> Dict[int, List[int]]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}

    if not isinstance(raw, Mapping):
        return {}

    result: Dict[int, List[int]] = {}
    for key, values in raw.items():
        ptype = _parse_piece_key(key)
        if ptype is None:
            continue
        if not isinstance(values, Iterable):
            continue
        result[ptype] = _ensure_length(values)
    return result


@lru_cache(maxsize=None)
def _load_layer(layer: str, phase: str) -> Dict[int, List[int]]:
    filename = LAYER_FILENAMES[layer][phase]
    data = _load_json_table(WEIGHTS_DIR / filename)
    if data:
        return data
    return _default_layer(layer, phase)


def _combine_layer_tables(tables: Sequence[Dict[int, List[int]]]) -> Dict[int, tuple[int, ...]]:
    combined: Dict[int, tuple[int, ...]] = {}
    for ptype in PIECE_TYPES:
        accum = _empty_table()
        for table in tables:
            values = table.get(ptype)
            if not values:
                continue
            for idx, value in enumerate(values):
                accum[idx] += int(value)
        combined[ptype] = tuple(accum)
    return combined


@lru_cache(maxsize=None)
def _combined_tables_for_phase(phase: str) -> Dict[int, tuple[int, ...]]:
    tables = [_load_layer(layer, phase) for layer in LAYERS]
    return _combine_layer_tables(tables)


def reload_tables() -> None:
    """Clear cached PST data so that the next access reloads from disk."""
    _load_layer.cache_clear()
    _combined_tables_for_phase.cache_clear()


def game_phase_from_board(board: chess.Board) -> str:
    """Return either ``"midgame"`` or ``"endgame"`` based on ``board``."""
    phase = GamePhaseDetector.detect(board)
    return "endgame" if phase == "endgame" else "midgame"


def effective_pst_for_piece(
    piece_type: int,
    *,
    board: chess.Board | None = None,
    phase: str | None = None,
) -> tuple[int, ...]:
    """Return the effective PST for ``piece_type``.

    Either ``board`` or ``phase`` must be provided.  ``phase`` should be
    ``"midgame"`` or ``"endgame"``; ``board`` is used to infer the phase via
    :func:`game_phase_from_board` when ``phase`` is omitted.
    """
    if phase is None:
        if board is None:
            raise ValueError("either board or phase must be provided")
        phase = game_phase_from_board(board)
    if phase not in PHASES:
        raise ValueError(f"unknown game phase: {phase}")
    tables = _combined_tables_for_phase(phase)
    return tables.get(piece_type, tuple(_empty_table()))


def all_effective_psts(
    *,
    board: chess.Board | None = None,
    phase: str | None = None,
) -> Dict[int, tuple[int, ...]]:
    """Return effective PSTs for all piece types for the selected phase."""
    if phase is None:
        if board is None:
            raise ValueError("either board or phase must be provided")
        phase = game_phase_from_board(board)
    if phase not in PHASES:
        raise ValueError(f"unknown game phase: {phase}")
    return dict(_combined_tables_for_phase(phase))
