from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import json
import os
from pathlib import Path
from typing import Dict, IO

try:  # pragma: no cover - platform-specific import
    import fcntl  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import portalocker  # type: ignore
except Exception:  # pragma: no cover
    portalocker = None  # type: ignore[assignment]

try:  # pragma: no cover - Windows
    import msvcrt  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    msvcrt = None  # type: ignore[assignment]

# Path to stats file relative to repository root
STATS_PATH = Path(__file__).resolve().parents[1] / "stats" / "usage_counts.json"


def lock_exclusive(f: IO[str]) -> None:
    """Acquire an exclusive lock for file *f*."""
    if fcntl:
        fcntl.flock(f, fcntl.LOCK_EX)
    elif portalocker:
        portalocker.lock(f, portalocker.LockFlags.EXCLUSIVE)
    elif msvcrt:
        # msvcrt.locking works relative to current file position
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
    else:  # pragma: no cover - no locking available
        logger.warning("File locking is not supported on this platform.")


def lock_shared(f: IO[str]) -> None:
    """Acquire a shared lock for file *f*."""
    if fcntl:
        fcntl.flock(f, fcntl.LOCK_SH)
    elif portalocker:
        portalocker.lock(f, portalocker.LockFlags.SHARED)
    elif msvcrt:
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_RLCK, 1)
    else:  # pragma: no cover - no locking available
        logger.warning("File locking is not supported on this platform.")


def unlock(f: IO[str]) -> None:
    """Release any lock held on file *f*."""
    if fcntl:
        fcntl.flock(f, fcntl.LOCK_UN)
    elif portalocker:
        portalocker.unlock(f)
    elif msvcrt:
        f.seek(0)
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:  # pragma: no cover - no locking available
        logger.warning("File locking is not supported on this platform.")


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
        lock_exclusive(f)
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
        unlock(f)


def read_usage() -> Dict[str, int]:
    """Return the usage counters loaded from the JSON file."""
    if not STATS_PATH.exists():
        return {}
    with open(STATS_PATH, "r", encoding="utf-8") as f:
        lock_shared(f)
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
        finally:
            unlock(f)
    return {k: int(v) for k, v in data.items()}
