"""Bridge to R-based board evaluation via :mod:`rpy2`.

An :class:`ImportError` is raised when the optional R bindings are missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import chess
import logging

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from rpy2 import robjects
except Exception:  # rpy2 may be missing in lightweight environments
    robjects = None  # type: ignore
    logger.debug(
        "R runtime or rpy2 is not available; install them to enable R evaluation."
    )


_FUNC_NAME = "eval_position_complex"
_loaded = False


def _ensure_loaded() -> None:
    """Load the R evaluation function if available."""
    global _loaded
    if _loaded:
        return
    if robjects is None:
        raise ImportError("rpy2 is not installed")
    script = Path(__file__).with_name(f"{_FUNC_NAME}.R")
    if not script.exists():
        logger.warning(
            "R evaluation script '%s' is missing; R evaluation disabled.", script.name
        )
        raise RuntimeError("missing R evaluation script")
    try:
        robjects.r["source"](str(script))
    except Exception as exc:
        logger.warning("Failed to source R script: %s", exc)
        raise RuntimeError("unable to source R evaluation script") from exc
    if _FUNC_NAME not in robjects.globalenv:
        logger.warning(
            "R function '%s' not found; check eval_position_complex.R", _FUNC_NAME
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
    returning its numeric result. ``ImportError`` is raised if :mod:`rpy2` is
    missing, and ``RuntimeError`` if the R runtime or evaluation script cannot
    be accessed.
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

