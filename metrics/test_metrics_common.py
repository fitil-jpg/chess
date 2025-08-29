import chess

from metrics_common import evaluate_survivability


def test_evaluate_survivability_counts_undefended_attacked_pieces() -> None:
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.B7, chess.Piece(chess.BISHOP, chess.BLACK))
    board.set_piece_at(chess.G5, chess.Piece(chess.KNIGHT, chess.BLACK))
    board.set_piece_at(chess.H4, chess.Piece(chess.PAWN, chess.WHITE))

    risk = evaluate_survivability(board)

    assert risk[chess.WHITE] == 1
    assert risk[chess.BLACK] == 3


def test_evaluate_survivability_ignores_defended_pieces() -> None:
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.B7, chess.Piece(chess.BISHOP, chess.BLACK))
    board.set_piece_at(chess.D3, chess.Piece(chess.PAWN, chess.WHITE))

    risk = evaluate_survivability(board)

    assert risk[chess.WHITE] == 0
    assert risk[chess.BLACK] == 0
