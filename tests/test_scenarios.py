from scenarios import detect_scenarios
from fen_handler import fen_to_board_state


def test_isolated_pawn():
    board = fen_to_board_state("8/8/8/8/3P4/8/8/8 w - - 0 1")
    scenarios = detect_scenarios(board)
    assert any(s["id"] == "isolated_pawn" and s["square"] == "d4" for s in scenarios)


def test_knight_fork():
    board = fen_to_board_state("8/3q1r2/8/4N3/8/8/8/8 w - - 0 1")
    scenarios = detect_scenarios(board)
    assert any(s["id"] == "knight_fork" and s["square"] == "e5" for s in scenarios)


def test_no_scenarios_on_startpos():
    board = fen_to_board_state("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    scenarios = detect_scenarios(board)
    assert scenarios == []
