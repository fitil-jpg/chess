import pytest

chess = pytest.importorskip("chess")
if not hasattr(chess, "Board"):
    pytest.skip("python-chess not installed", allow_module_level=True)
from core.evaluator import Evaluator
from chess_ai.chess_bot import ChessBot


def test_move_reduces_unprotected_king_squares():
    board = chess.Board.empty()
    board.set_piece_at(chess.G1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.F3, chess.Piece(chess.KNIGHT, chess.WHITE))
    board.set_piece_at(chess.H4, chess.Piece(chess.QUEEN, chess.BLACK))
    board.turn = chess.WHITE

    evaluator = Evaluator(board)
    king_sq = board.king(chess.WHITE)
    before_zone = evaluator.piece_zone(board, king_sq, radius=2)
    before = sum(
        1
        for sq in before_zone
        if board.is_attacked_by(chess.BLACK, sq)
        and not board.is_attacked_by(chess.WHITE, sq)
    )

    move = chess.Move.from_uci("f3h4")
    temp = board.copy()
    temp.push(move)
    new_king_sq = temp.king(chess.WHITE)
    after_zone = evaluator.piece_zone(temp, new_king_sq, radius=2)
    after = sum(
        1
        for sq in after_zone
        if temp.is_attacked_by(chess.BLACK, sq)
        and not temp.is_attacked_by(chess.WHITE, sq)
    )

    assert after < before

    bot = ChessBot(chess.WHITE)
    score, reasons = bot.evaluate_move(board, move)
    assert "improves king zone" in reasons
