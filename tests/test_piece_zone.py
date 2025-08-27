import pytest

chess = pytest.importorskip("chess")
if not hasattr(chess, "Board"):
    pytest.skip("python-chess not installed", allow_module_level=True)
from core.evaluator import Evaluator


def test_piece_zone_knight_circle():
    board = chess.Board.empty()
    board.set_piece_at(chess.D4, chess.Piece(chess.KNIGHT, chess.WHITE))
    zone = Evaluator.piece_zone(board, chess.D4, radius=2)
    assert chess.C2 in zone
    assert chess.A1 not in zone


def test_piece_zone_queen_lines():
    board = chess.Board.empty()
    board.set_piece_at(chess.D4, chess.Piece(chess.QUEEN, chess.WHITE))
    zone = Evaluator.piece_zone(board, chess.D4, radius=2)
    assert chess.D6 in zone
    assert chess.F6 in zone
    assert chess.C6 not in zone
