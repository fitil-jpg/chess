class BoardAnalyzer:
    def __init__(self, board):
        self.board = board

    def get_all_attacks(self, color):
        attacks = set()
        color_flag = color if isinstance(color, bool) else (color == 'white')
        for piece in self.board.get_pieces(color_flag):
            attacks.update(piece.get_attacked_squares(self.board))
        return attacks

    def get_threat_map(self):
        return {
            'white': self.get_all_attacks('white'),
            'black': self.get_all_attacks('black')
        }

    def get_defense_map(self, color):
        defenses = set()
        color_flag = color if isinstance(color, bool) else (color == 'white')
        for piece in self.board.get_pieces(color_flag):
            defenses.update(piece.get_defended_squares(self.board))
        return defenses
