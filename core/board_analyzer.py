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

    def get_defense_map(self, color=None):
        """Return squares defended by each colour.

        When ``color`` is provided (``"white"`` or ``"black"``) a set of
        defended squares for that colour is returned.  With the default of
        ``None`` a mapping for both colours is produced, mirroring the structure
        of :meth:`get_threat_map`.
        """

        def collect(side):
            defended = set()
            for piece in self.board.get_pieces(side):
                defended.update(piece.get_defended_squares(self.board))
            return defended

        if color is None:
            return {
                'white': collect('white'),
                'black': collect('black'),
            }

        return collect(color)
