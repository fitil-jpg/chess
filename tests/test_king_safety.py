import chess
from core.evaluator import Evaluator


def test_king_safety_score():
    board = chess.Board()
    # Initial position should be neutral
    assert Evaluator.king_safety(board, chess.WHITE) == 0

    # Remove one of the shield pawns and add an attacking enemy queen
    board.remove_piece_at(chess.F2)
    board.remove_piece_at(chess.D8)
    board.set_piece_at(chess.H4, chess.Piece(chess.QUEEN, chess.BLACK))

    score = Evaluator.king_safety(board, chess.WHITE)
    assert score < 0
