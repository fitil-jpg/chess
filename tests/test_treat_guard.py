import chess

from chess_ai.treat_guard import enemy_two_move_fork_risk


def test_en_passant_corridor_detected():
    board = chess.Board("4k3/8/8/8/5p1p/8/6P1/4K3 b - - 0 1")
    risk, tag, r1, r2 = enemy_two_move_fork_risk(board, chess.WHITE)
    assert risk
    assert tag == "P:ep-corridor"
    assert r1 == chess.Move.from_uci("f4f3")
    assert r2 == chess.Move.from_uci("h4g3")


def test_en_passant_corridor_absent():
    board = chess.Board("4k3/8/8/8/5p2/8/6P1/4K3 b - - 0 1")
    risk, tag, r1, r2 = enemy_two_move_fork_risk(board, chess.WHITE)
    assert not risk
    assert tag == ""
    assert r1 is None and r2 is None

