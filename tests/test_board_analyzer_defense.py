import chess

from core.board_analyzer import BoardAnalyzer
from .test_piece_attacks import make_piece


class WrappedBoard:
    def __init__(self, board: chess.Board):
        self.board = board
        self.pieces = [make_piece(board, sq) for sq in board.piece_map()]

    def attacks(self, square: int):
        return self.board.attacks(square)

    def piece_at(self, square: int):
        return self.board.piece_at(square)

    def get_pieces(self, color=None):
        if color is None:
            return list(self.pieces)
        color_code = chess.WHITE if color == 'white' else chess.BLACK
        return [p for p in self.pieces if p.color == color_code]


def test_rook_defends_pawn_from_fen():
    fen = "k7/8/3P4/8/3R4/8/8/K7 w - - 0 1"
    board = chess.Board(fen)
    wrapped = WrappedBoard(board)
    analyzer = BoardAnalyzer(wrapped)
    defense_map = analyzer.get_defense_map()
    assert defense_map['white'] == {chess.D6}
    assert defense_map['black'] == set()
