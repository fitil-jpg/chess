import chess

from core.board_analyzer import BoardAnalyzer
from core.piece import piece_class_factory


class AnalysisBoard(chess.Board):
    def get_pieces(self, color=None):
        pieces = []
        for sq, piece in self.piece_map().items():
            pos = (chess.square_rank(sq), chess.square_file(sq))
            pieces.append(piece_class_factory(piece, pos))
        if color is None:
            return pieces
        color_flag = color if isinstance(color, bool) else (color == 'white')
        return [p for p in pieces if p.color == color_flag]


def test_rook_defends_pawn():
    board = AnalysisBoard("8/8/8/8/8/8/P7/R7 w - - 0 1")
    analyzer = BoardAnalyzer(board)
    defenses = analyzer.get_defense_map('white')
    assert chess.A2 in defenses
