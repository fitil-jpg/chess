from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

import fcntl

# Path to stats file relative to repository root
STATS_PATH = Path(__file__).resolve().parents[1] / "stats" / "usage_counts.json"


def record_usage(path: str) -> None:
    """Increment the usage counter for *path*.

    The counters are stored in ``stats/usage_counts.json`` relative to the
    repository root.  The file and its parent directory are created if they do
    not already exist.  File locking is used to prevent concurrent writes from
    corrupting the JSON data.
    """
    STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STATS_PATH.exists():
        STATS_PATH.write_text("{}", encoding="utf-8")

    with open(STATS_PATH, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            counts = json.load(f)
        except json.JSONDecodeError:
            counts = {}
        counts[path] = counts.get(path, 0) + 1
        f.seek(0)
        json.dump(counts, f)
        f.truncate()
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f, fcntl.LOCK_UN)


def read_usage() -> Dict[str, int]:
    """Return the usage counters loaded from the JSON file."""
    if not STATS_PATH.exists():
        return {}
    with open(STATS_PATH, "r", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return {k: int(v) for k, v in data.items()}
