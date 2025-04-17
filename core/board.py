class Board:
    def __init__(self):
        self.pieces = []

    def place_piece(self, piece):
        self.pieces.append(piece)

    def remove_piece(self, piece):
        self.pieces.remove(piece)

    def get_state(self):
        return [(p.symbol, p.position) for p in self.pieces]

    def get_all_pieces(self):
        return self.pieces

    def get_attackers(self, color, square):
        return [p for p in self.pieces if p.color == color and square in p.get_attacked_squares(self)]