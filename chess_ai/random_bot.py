import random

class RandomBot:
    def __init__(self, color: bool):
        self.color = color

    def choose_move(self, board, debug: bool = False):
        """Return a random legal move with low confidence."""

        moves = list(board.legal_moves)
        if not moves:
            return None, 0.0
        move = random.choice(moves)
        # Random decisions are inherently uncertain → very low confidence.
        return move, 0.0
