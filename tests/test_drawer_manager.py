import chess

from ui.drawer_manager import DrawerManager


def test_scenario_overlay_added():
    board = chess.Board("8/8/8/8/3P4/8/8/8 w - - 0 1")
    dm = DrawerManager()
    dm.collect_overlays({}, board)
    sq = chess.parse_square("d4")
    row = 7 - chess.square_rank(sq)
    col = chess.square_file(sq)
    assert any(t == "scenario" for t, _ in dm.overlays.get((row, col), []))
