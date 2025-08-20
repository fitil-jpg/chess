class BoardAnalyzer:
    def __init__(self, board):
        self.board = board

    def get_all_attacks(self, color):
        attacks = set()
        for piece in self.board.get_pieces(color):
            squares = piece.get_attacked_squares(self.board)
            attacks.update(squares)
        return attacks

    def get_threat_map(self):
        return {
            'white': self.get_all_attacks('white'),
            'black': self.get_all_attacks('black')
        }

    def _collect_defenses(self, color):
        """Gather defended squares for ``color`` pieces."""
        defenses = set()
        for piece in self.board.get_pieces(color):
            defenses.update(piece.get_defended_squares(self.board))
        return defenses

    def get_defense_map(self):
        """Return mapping of color to defended squares on the board."""
        return {
            'white': self._collect_defenses('white'),
            'black': self._collect_defenses('black')
        }
