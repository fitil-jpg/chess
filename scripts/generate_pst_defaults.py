#!/usr/bin/env python3
"""Generate default piece-square table (PST) weight files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pst_tables import PST_MG

PIECE_TYPES = (1, 2, 3, 4, 5, 6)

PIECE_SYMBOLS = {
    1: "P",
    2: "N",
    3: "B",
    4: "R",
    5: "Q",
    6: "K",
}

# --- Helpers -------------------------------------------------------------------


def _rank_based_table(values: Sequence[int]) -> list[int]:
    table: list[int] = []
    for rank in range(8):
        bonus = values[rank]
        table.extend([bonus] * 8)
    return table


KING_ENDGAME = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -20, -10,  10,  20,  20,  10, -10, -20,
    -10,   0,  20,  30,  30,  20,   0, -10,
     -5,  10,  30,  40,  40,  30,  10,  -5,
    -10,   0,  20,  30,  30,  20,   0, -10,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -50, -40, -30, -20, -20, -30, -40, -50,
]

PAWN_ENDGAME = _rank_based_table([0, 10, 15, 25, 40, 60, 80, 0])


def _symbol_table(data: Dict[int, Sequence[int]]) -> Dict[str, list[int]]:
    return {PIECE_SYMBOLS[ptype]: list(values) for ptype, values in data.items()}


# --- Main ----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing files instead of keeping them",
    )
    args = parser.parse_args()

    weights_dir = REPO_ROOT / "weights"
    weights_dir.mkdir(exist_ok=True)

    base_midgame = {ptype: list(PST_MG.get(ptype, [0] * 64)) for ptype in PIECE_TYPES}
    base_endgame = {
        1: PAWN_ENDGAME,
        2: list(PST_MG.get(2, [0] * 64)),
        3: list(PST_MG.get(3, [0] * 64)),
        4: list(PST_MG.get(4, [0] * 64)),
        5: list(PST_MG.get(5, [0] * 64)),
        6: KING_ENDGAME,
    }
    zero_tables = {ptype: [0] * 64 for ptype in PIECE_TYPES}

    outputs = {
        "pst_base_mg.json": _symbol_table(base_midgame),
        "pst_base_eg.json": _symbol_table(base_endgame),
        "pst_user_mg.json": _symbol_table(zero_tables),
        "pst_user_eg.json": _symbol_table(zero_tables),
        "pst_learned_mg.json": _symbol_table(zero_tables),
        "pst_learned_eg.json": _symbol_table(zero_tables),
    }

    for name, data in outputs.items():
        path = weights_dir / name
        if path.exists() and not args.force:
            print(f"Skipping {name} (already exists; use --force to overwrite)")
            continue
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        print(f"Wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
