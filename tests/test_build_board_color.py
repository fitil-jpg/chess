import chess

from core.piece import _build_board


def test_build_board_preserves_white_color():
    pc_board = chess.Board()
    pc_board.clear()
    pc_board.set_piece_at(chess.E4, chess.Piece(chess.KING, chess.WHITE))

    board = _build_board(pc_board)

    whites = board.get_pieces('white')
    assert len(whites) == 1
    assert whites[0].color == 'white'
