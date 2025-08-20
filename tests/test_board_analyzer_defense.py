from core.board import Board
from core.piece import Pawn, Rook
from core.board_analyzer import BoardAnalyzer


def test_rook_defends_pawn():
    board = Board()
    board.place_piece(Rook('white', 'a1'))
    board.place_piece(Pawn('white', 'a2'))
    analyzer = BoardAnalyzer(board)
    defense = analyzer.get_defense_map('white')
    assert 'a2' in defense
    assert defense == {'a2'}

