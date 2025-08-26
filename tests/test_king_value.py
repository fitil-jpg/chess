import chess

from chess_ai.chess_bot import ChessBot, calculate_king_value


def _base_board():
    board = chess.Board()
    board.clear_board()
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    return board


def test_dynamic_king_value_scales_and_enemy_queen():
    board = _base_board()
    board.set_piece_at(chess.A7, chess.Piece(chess.QUEEN, chess.BLACK))

    base = calculate_king_value(board, chess.WHITE)
    assert base == 0

    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    with_pawn = calculate_king_value(board, chess.WHITE)
    assert with_pawn > base

    board.remove_piece_at(chess.A7)
    without_queen = calculate_king_value(board, chess.WHITE)
    assert without_queen == int(with_pawn * 0.85)


def test_evaluation_uses_dynamic_king_value():
    board = _base_board()
    board.set_piece_at(chess.E2, chess.Piece(chess.PAWN, chess.BLACK))

    bot = ChessBot(chess.WHITE)
    move = chess.Move.from_uci("e1e2")

    score_no_allies, _ = bot.evaluate_move(board, move)

    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    score_with_pawn, _ = bot.evaluate_move(board, move)

    assert score_with_pawn < score_no_allies
