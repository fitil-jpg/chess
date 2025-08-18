"""Shared context dataclass for chess agents."""

from dataclasses import dataclass


@dataclass
class GameContext:
    """Shared positional metrics available to all agents."""

    material_diff: int
    mobility: int
    king_safety: int

