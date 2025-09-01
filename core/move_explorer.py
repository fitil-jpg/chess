import logging
logger = logging.getLogger(__name__)

class MoveExplorer:
    def __init__(self, board):
        self.board = board

    def get_all_legal_moves(self, color):
        legal_moves = []
        for piece in self.board.get_all_pieces():
            if piece.color != color:
                continue
            for target in piece.get_attacked_squares(self.board):
                legal_moves.append((piece.position, target))
        return legal_moves
