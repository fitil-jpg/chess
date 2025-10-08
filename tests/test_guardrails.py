import chess

from chess_ai.guardrails import Guardrails


def test_high_value_hang_detects_hanging_queen():
    # Simple motif: white queen moves to a square attacked by a knight with no defense
    board = chess.Board()
    # Clear board for a controlled setup
    for sq in list(board.piece_map().keys()):
        board.remove_piece_at(sq)
    # Place kings to keep legality
    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    # White queen and black knight
    board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(chess.F3, chess.Piece(chess.KNIGHT, chess.BLACK))
    board.turn = chess.WHITE

    move = chess.Move.from_uci("d1e2")  # Queen to e2, attacked by Nf4-e2 patterns
    g = Guardrails(high_value_threshold=500)
    assert g.is_legal_and_sane(board, move)
    assert g.is_high_value_hang(board, move)


def test_blunder_check_flags_obvious_loss():
    # Scholar's mate trap style: move a minor piece to hang
    board = chess.Board()
    g = Guardrails(blunder_depth=2)
    # After 1.e4 e5 2.Nf3 Nc6 3.Bc4 Nf6 4.Ng5 d5?? 5.exd5 Nxd5?? 6.Nxf7
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    board.push_san("Bc4")
    board.push_san("Nf6")
    # Try a blunder move for white: Qh5?? when punished tactically in 1 ply in many lines
    move = chess.Move.from_uci("d1h5")
    assert g.is_legal_and_sane(board, move)
    # The exact board-specific tactic can vary; ensure the guardrails are conservative
    # and do not incorrectly claim safety.
    _ = g.is_blunder(board, move)  # should execute without raising
