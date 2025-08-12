import random

class RandomBot:
    def __init__(self, color):
        self.color = color

    def choose_move(self, board, debug=False):
        moves = list(board.legal_moves)
        if not moves:
            return (None, "no moves") if debug else None
        move = random.choice(moves)
        return (move, "random") if debug else move
