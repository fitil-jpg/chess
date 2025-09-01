"""Colour definitions for module usage visualisations."""

import logging
logger = logging.getLogger(__name__)

from PySide6.QtGui import QColor

# Order of priority used when extracting a module key from a reason string.
REASON_PRIORITY = [
    "AGGRESSIVE", "SAFE_CHECK", "FORTIFY", "COW",
    "DEPTH3", "DEPTH2", "ENDGAME", "CENTER",
    "UTILITY", "RANDOM", "LEGACY", "THREAT",
]

# Mapping from module key to colours used in charts / timelines.
MODULE_COLORS = {
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
