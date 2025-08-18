"""Bridge to R-based evaluation via rpy2."""

from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from rpy2 import robjects
except Exception:  # rpy2 may be missing in lightweight environments
    robjects = None  # type: ignore


def r_evaluate(fen: str) -> float:
    """Evaluate position ``fen`` using an R function named ``r_eval``.

    The R environment must define ``r_eval`` that accepts a FEN string and
    returns a single numeric value.  If :mod:`rpy2` or the function is not
    available, ``RuntimeError`` is raised.
    """
    if robjects is None:
        raise RuntimeError("rpy2 is not installed")
    if "r_eval" not in robjects.globalenv:
        raise RuntimeError("R function 'r_eval' not found in global env")
    r_func = robjects.globalenv["r_eval"]
    return float(r_func(fen)[0])

