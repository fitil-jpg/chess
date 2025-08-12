"""
context.py — зберігає додатковий контекст AI: фазу гри, стиль, статистику, памʼять тощо.

Мінімальна версія: зберігає тільки фазу гри ("opening", "middlegame", "endgame").
"""

class Context:
    def __init__(self):
        self.phase = "opening"
        self.style = "balanced"  # або "aggressive", "defensive"
        self.history = []        # список ходів або подій (опційно)

    def update_phase(self, board):
        """
        Оновлює фазу гри на основі кількості фігур чи інших ознак.
        """
        pieces = sum(1 for sq in board.piece_map().values() if sq.piece_type != 1)  # не пішки
        if pieces > 10:
            self.phase = "opening"
        elif pieces > 4:
            self.phase = "middlegame"
        else:
            self.phase = "endgame"
