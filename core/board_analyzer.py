from .piece import build_chess_board


class BoardAnalyzer:
    def __init__(self, board):
        self.board = board

    def get_all_attacks(self, color):
        chess_board = build_chess_board(self.board)
        attacks = set()
        for piece in self.board.get_pieces(color):
            squares = piece.get_attacked_squares(self.board, chess_board)
            attacks.update(squares)
        return attacks

    def get_threat_map(self):
        return {
            'white': self.get_all_attacks('white'),
            'black': self.get_all_attacks('black')
        }
    
    def get_defense_map(self):
        """Return mapping of color to defended squares on the board."""
        chess_board = build_chess_board(self.board)
        defense_map = {'white': set(), 'black': set()}
        for color in ('white', 'black'):
            for piece in self.board.get_pieces(color):
                defense_map[color].update(
                    piece.get_defended_squares(self.board, chess_board)
                )
        return defense_map
