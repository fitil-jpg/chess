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
