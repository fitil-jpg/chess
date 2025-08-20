import chess
from core.metrics import MetricsManager


def make_empty_board():
    board = chess.Board.empty()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    return board


def test_count_attacked_squares():
    board = make_empty_board()
    board.set_piece_at(chess.C3, chess.Piece(chess.KNIGHT, chess.WHITE))
    board.set_piece_at(chess.F6, chess.Piece(chess.KNIGHT, chess.BLACK))
    manager = MetricsManager(board)
    assert manager.count_attacked_squares() == 0


def test_count_defended_pieces():
    board = make_empty_board()
    board.set_piece_at(chess.E2, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(chess.A8, chess.Piece(chess.ROOK, chess.BLACK))
    manager = MetricsManager(board)
    # White rook defended by the king, black rook undefended
    assert manager.count_defended_pieces() == 1


def test_evaluate_center_control():
    board = make_empty_board()
    board.set_piece_at(chess.D4, chess.Piece(chess.KNIGHT, chess.WHITE))
    manager = MetricsManager(board)
    assert manager.evaluate_center_control() == 1


def test_evaluate_king_safety():
    board = make_empty_board()
    board.set_piece_at(chess.E7, chess.Piece(chess.QUEEN, chess.WHITE))
    manager = MetricsManager(board)
    # Queen on e7 attacks all squares around the black king
    assert manager.evaluate_king_safety() == 5


def test_evaluate_pawn_structure():
    board = make_empty_board()
    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.A3, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.BLACK))
    manager = MetricsManager(board)
    assert manager.evaluate_pawn_structure() == -2
