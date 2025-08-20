from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

REQUIRED_KEYS = {"moves", "fens", "modules_w", "modules_b", "result"}


def load_runs(path: str) -> List[Dict[str, Any]]:
    """Load run JSON files from *path* and include save timestamps.

    Each JSON file must contain the keys defined in :data:`REQUIRED_KEYS`.
    The returned run dictionaries additionally include a ``date`` field with
    the file's modification time encoded via :meth:`datetime.isoformat`.
    """
    runs: List[Dict[str, Any]] = []
    base_path = Path(path)

    for file in sorted(base_path.glob("*.json")):
        with file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(
                f"Missing keys in {file.name}: {', '.join(sorted(missing))}"
            )

        runs.append(
            {
                "game_id": file.stem,
                "moves": data["moves"],
                "fens": data["fens"],
                "modules_w": data["modules_w"],
                "modules_b": data["modules_b"],
                "result": data["result"],
                "date": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
            }
        )

    return runs
