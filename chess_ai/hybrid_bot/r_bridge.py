"""Bridge to R-based board evaluation via :mod:`rpy2`."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

import chess
import logging

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from rpy2 import robjects
    _missing_rpy2 = False
except ModuleNotFoundError as exc:  # rpy2 missing or partially installed
    robjects = None  # type: ignore
    _missing_rpy2 = exc.name == "rpy2"
    if _missing_rpy2:
        logger.debug(
            "R runtime or rpy2 is not available; install them to enable R evaluation."
        )
    else:
        logger.debug(
            "rpy2 is present but missing optional components; falling back to Python eval."
        )
except Exception:  # pragma: no cover - other initialisation errors
    robjects = None  # type: ignore
    _missing_rpy2 = False
    logger.debug(
        "rpy2 is present but cannot be initialised; falling back to Python eval."
    )


_FUNC_NAME = "eval_position_complex"
_loaded = False


def _ensure_loaded() -> bool:
    """Load the R evaluation function if available.

    Returns ``True`` if the function was loaded successfully, ``False``
    otherwise.  Errors are logged but not raised, allowing callers to fall back
    to a Python implementation when R is missing.
    """
    global _loaded
    if _loaded:
        return True
    if robjects is None:
        return False
    script = Path(__file__).with_name(f"{_FUNC_NAME}.R")
    if not script.exists():
        logger.warning(
            "R evaluation script '%s' is missing; R evaluation disabled.", script.name
        )
        return False
    try:  # pragma: no cover - heavy dependency
        robjects.r["source"](str(script))
    except Exception as exc:
        logger.warning("Failed to source R script: %s", exc)
        return False
    if _FUNC_NAME not in robjects.globalenv:
        logger.warning(
            "R function '%s' not found; check eval_position_complex.R", _FUNC_NAME
        )
        return False
    _loaded = True
    return True


def eval_board(
    board: chess.Board, enemy_material: Mapping[str, float] | None = None
) -> float:
    """Return evaluation score for ``board`` using R if possible.

    If :mod:`rpy2` or the R evaluation script is unavailable, a lightweight
    Python evaluation is used as a fallback.  A ``RuntimeError`` is raised only
    when :mod:`rpy2` itself cannot be imported.
    """
    if robjects is None:
        if _missing_rpy2:
            raise RuntimeError("rpy2 is not installed")
        from .evaluation import evaluate_position

        return evaluate_position(board)
    if not _ensure_loaded():
        from .evaluation import evaluate_position

        return evaluate_position(board)
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

