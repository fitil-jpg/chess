from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_KEYS = {"moves", "fens", "modules_w", "modules_b"}
DEFAULT_RESULT = "*"


def load_runs(path: str) -> List[Dict[str, Any]]:
    """Load all run JSON files from *path*.

    Each JSON file must contain the keys defined in :data:`REQUIRED_KEYS`.
    The returned list contains dictionaries with those values plus a
    ``game_id`` derived from the file name (without extension).

    Parameters
    ----------
    path:
        Directory that holds run ``.json`` files.

    Returns
    -------
    List[Dict[str, Any]]
        A list of run objects with ``game_id`` and required fields.

    Raises
    ------
    ValueError
        If a JSON file is missing any required keys.
    """
    runs: List[Dict[str, Any]] = []
    base_path = Path(path)

    for file in sorted(base_path.glob("*.json")):
        with file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        missing = REQUIRED_KEYS - data.keys()
        if missing:
            raise ValueError(f"Missing keys in {file.name}: {', '.join(sorted(missing))}")

        runs.append(
            {
                "game_id": file.stem,
                "moves": data["moves"],
                "fens": data["fens"],
                "modules_w": data["modules_w"],
                "modules_b": data["modules_b"],
                "result": data.get("result", DEFAULT_RESULT),
            }
        )

    return runs
