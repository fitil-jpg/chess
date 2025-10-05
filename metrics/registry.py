"""Simple registry for board evaluators.

Evaluators are callables that accept a ``board`` and return a value (number or
structured data). ``evaluate_all(board)`` executes the registered evaluators and
returns a mapping ``{name: value}``.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: Dict[str, Callable[[Any], Any]] = {}

    # ------------------------------------------------------------------
    def register(self, name: str, func: Callable[[Any], Any], *, override: bool = False) -> None:
        if not callable(func):
            raise TypeError("evaluator must be callable")
        if not override and name in self._evaluators:
            raise ValueError(f"evaluator '{name}' already registered")
        self._evaluators[name] = func

    def unregister(self, name: str) -> None:
        self._evaluators.pop(name, None)

    def clear(self) -> None:
        self._evaluators.clear()

    def list(self) -> list[str]:
        return sorted(self._evaluators)

    def has_any(self) -> bool:
        return bool(self._evaluators)

    # ------------------------------------------------------------------
    def evaluate_all(self, board: Any) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for name, func in list(self._evaluators.items()):
            try:
                results[name] = func(board)
            except Exception:
                # Evaluators are best-effort; ignore failures so callers are robust
                continue
        return results


REGISTRY = EvaluatorRegistry()


# ---------------------------------------------------------------------------
# Default evaluators (registered if their providers are available)
# ---------------------------------------------------------------------------

def _try_register_defaults() -> None:
    # evaluation.evaluate(board) -> (score, details)
    try:
        from evaluation import evaluate as _evaluate  # type: ignore

        def _eval_total(board: Any) -> int:
            score, _ = _evaluate(board)
            return int(score)

        REGISTRY.register("eval_total", _eval_total, override=True)
    except Exception:
        pass

    # Optional: attack balance via evaluation.attacked_squares_metrics
    try:
        from evaluation import attacked_squares_metrics as _att_metrics  # type: ignore

        def _delta_attacks(board: Any) -> int:
            return int(_att_metrics(board).get("delta_attacks", 0))

        REGISTRY.register("delta_attacks", _delta_attacks, override=True)
    except Exception:
        pass


_try_register_defaults()


# Public helpers --------------------------------------------------------------

def register(name: str, func: Callable[[Any], Any], *, override: bool = False) -> None:
    REGISTRY.register(name, func, override=override)


def evaluate_all(board: Any) -> Dict[str, Any]:
    return REGISTRY.evaluate_all(board)


def list_evaluators() -> list[str]:
    return REGISTRY.list()
