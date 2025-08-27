import chess
from metrics_common import evaluate_pressure, evaluate_synergy

def test_evaluate_pressure() -> None:
    """Pressure accounts for attacked piece values."""
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A8, chess.Piece(chess.QUEEN, chess.BLACK))
    board.set_piece_at(chess.B4, chess.Piece(chess.BISHOP, chess.BLACK))
    board.set_piece_at(chess.E1, chess.Piece(chess.KNIGHT, chess.WHITE))
    assert evaluate_pressure(board) == 6


def test_evaluate_synergy() -> None:
    """Synergy counts squares attacked by multiple same-colour pieces."""
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.C3, chess.Piece(chess.KNIGHT, chess.WHITE))
    board.set_piece_at(chess.E3, chess.Piece(chess.KNIGHT, chess.WHITE))
    assert evaluate_synergy(board) == 2
