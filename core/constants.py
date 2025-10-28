import logging
logger = logging.getLogger(__name__)

# core/constants.py
SYMBOLS = {
    "P": "♙", "R": "♖", "N": "♘", "B": "♗", "Q": "♕", "K": "♔",
    "p": "♟", "r": "♜", "n": "♞", "b": "♝", "q": "♛", "k": "♚"
}

# Thresholds for the dynamic bot.  When the material difference exceeds
# ``MATERIAL_DIFF_THRESHOLD`` the bot switches to an aggressive style.  If the
# king safety score drops below ``KING_SAFETY_THRESHOLD`` it prefers a
# fortification strategy.
MATERIAL_DIFF_THRESHOLD = 3
KING_SAFETY_THRESHOLD = 0

# Piece priority values for scoring
PIECE_PRIORITY = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0,
    'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0
}

# Fork pair priority for tactical evaluation
fork_pair_priority = {
    ('Q', 'K'): 100,
    ('R', 'K'): 80,
    ('Q', 'Q'): 90,
    ('R', 'Q'): 70,
    ('N', 'Q'): 60,
    ('B', 'Q'): 60,
    ('N', 'R'): 50,
    ('B', 'R'): 50
}

# Sigmoid multiplier for evaluation scaling
sigmoid_multiplier = 0.1