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
REASON_PRIORITY = [
    "AGGRESSIVE", "SAFE_CHECK", "FORTIFY", "COW",
    "WFC", "BSP", "PATTERN",
    "DEPTH3", "DEPTH2", "ENDGAME", "CENTER",
    "UTILITY", "RANDOM", "LEGACY", "THREAT",
]

# Mapping from module key to colours used in charts / timelines.
MODULE_COLORS = {
    "AGGRESSIVE": QColor(220, 53, 69),    # red
    "SAFE_CHECK": QColor(255, 159, 64),   # orange
    "FORTIFY":    QColor(13, 110, 253),   # blue
    "COW":        QColor(40, 167, 69),    # green
    "WFC":        QColor(23, 162, 184),   # cyan
    "BSP":        QColor(66, 139, 202),   # steel blue
    "PATTERN":    QColor(100, 181, 246),  # light blue
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
