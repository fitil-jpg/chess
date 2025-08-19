"""Bridge to R-based board evaluation via :mod:`rpy2`."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import chess
import warnings

try:  # pragma: no cover - optional dependency
    from rpy2 import robjects
except Exception:  # rpy2 may be missing in lightweight environments
    robjects = None  # type: ignore


_FUNC_NAME = "eval_position_complex"
_loaded = False


def _ensure_loaded() -> None:
    """Load the R evaluation function if available."""
    global _loaded
    if _loaded:
        return
    if robjects is None:
        warnings.warn("rpy2 or R is not installed; R evaluation disabled.")
        raise RuntimeError("rpy2 is not installed")
    script = Path(__file__).with_name(f"{_FUNC_NAME}.R")
    try:
        robjects.r["source"](str(script))
    except Exception as exc:
        warnings.warn(f"Failed to source R script: {exc}")
        raise RuntimeError("unable to source R evaluation script") from exc
    if _FUNC_NAME not in robjects.globalenv:
        warnings.warn(
            f"R function '{_FUNC_NAME}' not found; check eval_position_complex.R"
        )
        raise RuntimeError(
            f"R function '{_FUNC_NAME}' not found after sourcing"
        )
    _loaded = True


def eval_board(
    board: chess.Board, enemy_material: Mapping[str, float] | None = None
) -> float:
    """Return evaluation score for ``board`` using R's ``eval_position_complex``.

    Parameters
    ----------
    board:
        Board to evaluate.
    enemy_material:
        Optional mapping with keys ``"white"`` and ``"black"`` to modulate king
        safety based on remaining attacking material of each side. ``1``
        corresponds to full material; lower values reduce the impact of attacks.

    The function sources the accompanying R script and calls the R function,
    returning its numeric result.  ``RuntimeError`` is raised if :mod:`rpy2` or
    the R function is unavailable.
    """
    _ensure_loaded()
    r_func = robjects.globalenv[_FUNC_NAME]
    if enemy_material is None:
        res = r_func(board.fen())
    else:
        r_list = robjects.ListVector(enemy_material)
        res = r_func(board.fen(), r_list)
    return float(res[0])


def r_evaluate(fen: str, enemy_material: Mapping[str, float] | None = None) -> float:
    """Backward compatible FEN-based wrapper around :func:`eval_board`."""
    board = chess.Board(fen)
    return eval_board(board, enemy_material)

