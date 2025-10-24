"""Colour definitions for module usage visualisations.

This module gracefully degrades when PySide6 is unavailable (e.g., on servers).
In that case, a lightweight QColor shim is provided that preserves repr/tuple
behaviour expected by UI components, while keeping imports cheap for web_server.
"""

import logging
logger = logging.getLogger(__name__)

try:
    from PySide6.QtGui import QColor  # type: ignore
except Exception:  # pragma: no cover - headless/server environments
    class QColor:  # minimal shim
        def __init__(self, r: int, g: int, b: int):
            self._r, self._g, self._b = int(r), int(g), int(b)
        def getRgb(self):
            return (self._r, self._g, self._b, 255)
        def __iter__(self):
            yield from (self._r, self._g, self._b)
        def __repr__(self) -> str:
            return f"QColor({self._r}, {self._g}, {self._b})"
        # Convenience hex string for web contexts
        @property
        def hex(self) -> str:
            return f"#{self._r:02x}{self._g:02x}{self._b:02x}"

# Order of priority used when extracting a module key from a reason string.
# Include analysis engines and safety layers so they appear distinctly in
# timelines and charts.
REASON_PRIORITY = [
    "WFC", "BSP", "GUARD", "GUARDRAILS",
    "AGGRESSIVE", "SAFE_CHECK", "FORTIFY", "COW",
    "DEPTH3", "DEPTH2", "ENDGAME", "CENTER",
    "UTILITY", "RANDOM", "LEGACY", "THREAT",
]

# Mapping from module key to colours used in charts / timelines.
MODULE_COLORS = {
    # Engines / safety layers
    "WFC":       QColor(56, 189, 248),   # sky blue
    "BSP":       QColor(59, 130, 246),   # blue
    "GUARD":     QColor(16, 185, 129),   # emerald/teal
    "GUARDRAILS": QColor(5, 150, 105),   # darker teal
    "AGGRESSIVE": QColor(220, 53, 69),    # red
    "SAFE_CHECK": QColor(255, 159, 64),   # orange
    "FORTIFY":    QColor(13, 110, 253),   # blue
    "COW":        QColor(40, 167, 69),    # green
    "DEPTH3":     QColor(111, 66, 193),   # purple
    "DEPTH2":     QColor(153, 102, 255),  # light purple
    "ENDGAME":    QColor(102, 16, 242),   # indigo
    "CENTER":     QColor(108, 117, 125),  # grey
    "UTILITY":    QColor(20, 184, 166),   # teal
    "RANDOM":     QColor(255, 99, 132),   # pinkish red
    "LEGACY":     QColor(73, 80, 87),     # dark grey
    "THREAT":     QColor(255, 205, 86),   # yellow
    "OTHER":      QColor(201, 203, 207),  # light grey
}
