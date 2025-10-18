"""chess_ai package

Lightweight package initializer. Exposes key classes via lazy imports to
avoid importing heavy submodules at package import time (important for tests
that monkeypatch the ``chess`` module).
"""

import logging
logger = logging.getLogger(__name__)

__all__ = ["HybridOrchestrator", "HybridBot", "KingValueBot", "PieceMateBot", "WolframBot"]

def __getattr__(name: str):
    if name == "HybridOrchestrator":
        from .hybrid_bot import HybridOrchestrator
        return HybridOrchestrator
    if name == "HybridBot":
        from .bot_agent import HybridBot
        return HybridBot
    if name == "KingValueBot":
        from .king_value_bot import KingValueBot
        return KingValueBot
    if name == "PieceMateBot":
        from .piece_mate_bot import PieceMateBot
        return PieceMateBot
    if name == "WolframBot":
        from .wolfram_bot import WolframBot
        return WolframBot
    raise AttributeError(name)