import chess

from core.board_analyzer import BoardAnalyzer
from core.piece import piece_class_factory


class WrappedBoard:
    def __init__(self, board: chess.Board):
        self.board = board
        self.pieces = [
            piece_class_factory(piece, (chess.square_rank(sq), chess.square_file(sq)))
            for sq, piece in board.piece_map().items()
        ]

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


def test_knight_defends_pawn_with_boolean_colors():
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.D4, chess.Piece(chess.KNIGHT, chess.WHITE))
    board.set_piece_at(chess.F5, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.E6, chess.Piece(chess.KNIGHT, chess.BLACK))
    board.set_piece_at(chess.F4, chess.Piece(chess.PAWN, chess.BLACK))

    wrapped = WrappedBoard(board)
    analyzer = BoardAnalyzer(wrapped)
    defense_map = analyzer.get_defense_map()
    assert defense_map['white'] == {chess.F5}
    assert defense_map['black'] == {chess.F4}


def test_bishop_defends_pawn_with_boolean_colors():
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, chess.WHITE))
    board.set_piece_at(chess.D2, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.F8, chess.Piece(chess.BISHOP, chess.BLACK))
    board.set_piece_at(chess.E7, chess.Piece(chess.PAWN, chess.BLACK))

    wrapped = WrappedBoard(board)
    analyzer = BoardAnalyzer(wrapped)
    defense_map = analyzer.get_defense_map()
    assert defense_map['white'] == {chess.D2}
    assert defense_map['black'] == {chess.E7}
