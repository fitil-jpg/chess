from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

import chess


class PatternResponder:
    """Loads pattern templates and finds matching actions.

    A pattern is a mapping with two keys:
    ``situation`` – the piece placement portion of a FEN string,
    and ``action`` – an arbitrary response (usually a move in UCI format).
    """

    def __init__(self, patterns: List[Dict[str, Any]]) -> None:
        self.patterns = patterns

    @classmethod
    def from_file(cls, path: str | Path) -> "PatternResponder":
        """Create a responder from a JSON or YAML file."""
        p = Path(path)
        with p.open("r", encoding="utf8") as fh:
            if p.suffix in {".yaml", ".yml"}:
                if yaml is None:  # pragma: no cover - defensive
                    raise RuntimeError("PyYAML is required for YAML pattern files")
                data = yaml.safe_load(fh)
            else:
                data = json.load(fh)
        if isinstance(data, dict):
            patterns = data.get("patterns", [])
        else:
            patterns = data
        return cls(patterns)

    def match(self, board: chess.Board) -> Optional[str]:
        """Return the action for the current board state, if any."""
        layout = board.board_fen()
        for p in self.patterns:
            if p.get("situation") == layout:
                return p.get("action")
        return None