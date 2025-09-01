from __future__ import annotations

"""Utility for recording module usage counts.

The :func:`record_usage` function increments a counter associated with a module
path.  Counts are stored in a JSON file located in the user's home directory so
that they persist across runs without polluting the repository tree.
"""

from pathlib import Path
import json
from threading import Lock
from typing import Dict

USAGE_FILE = Path.home() / ".chess_usage.json"
_lock = Lock()


def _load_counts() -> Dict[str, int]:
    """Return the current usage counters."""
    try:
        with USAGE_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_counts(data: Dict[str, int]) -> None:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USAGE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)


def record_usage(module_path: str) -> None:
    """Record a usage event for *module_path*.

    Parameters
    ----------
    module_path:
        The file path of the module invoking this function, typically
        ``__file__``.
    """
    path = str(Path(module_path).resolve())
    with _lock:
        data = _load_counts()
        data[path] = data.get(path, 0) + 1
        _save_counts(data)


def read_usage() -> Dict[str, int]:
    """Return a copy of the current usage counters."""
    with _lock:
        return dict(_load_counts())


__all__ = ["record_usage", "read_usage"]
