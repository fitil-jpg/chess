"""Bridge to R-based board evaluation via :mod:`rpy2`."""

from __future__ import annotations

from pathlib import Path

import chess

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
        raise RuntimeError("rpy2 is not installed")
    script = Path(__file__).with_name(f"{_FUNC_NAME}.R")
    robjects.r["source"](str(script))
    if _FUNC_NAME not in robjects.globalenv:
        raise RuntimeError(f"R function '{_FUNC_NAME}' not found after sourcing")
    _loaded = True


def eval_board(board: chess.Board) -> float:
    """Return evaluation score for ``board`` using R's ``eval_position_complex``.

    The function sources the accompanying R script and calls the R function,
    returning its numeric result.  ``RuntimeError`` is raised if :mod:`rpy2` or
    the R function is unavailable.
    """
    _ensure_loaded()
    r_func = robjects.globalenv[_FUNC_NAME]
    return float(r_func(board.fen())[0])


def r_evaluate(fen: str) -> float:
    """Backward compatible FEN-based wrapper around :func:`eval_board`."""
    board = chess.Board(fen)
    return eval_board(board)

