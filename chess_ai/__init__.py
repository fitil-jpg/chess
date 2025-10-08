"""chess_ai package

Avoid importing heavy submodules at package import time to keep test and
runtime environments lightweight. Public symbols are exposed lazily via
``__getattr__`` when accessed.
"""

from __future__ import annotations

__all__ = ["HybridOrchestrator", "HybridBot", "KingValueBot"]


def __getattr__(name: str):  # pragma: no cover - thin lazy loader
    if name == "HybridOrchestrator":
        from .hybrid_bot import HybridOrchestrator
        return HybridOrchestrator
    if name == "HybridBot":
        from .bot_agent import HybridBot
        return HybridBot
    if name == "KingValueBot":
        from .king_value_bot import KingValueBot
        return KingValueBot
    raise AttributeError(name)