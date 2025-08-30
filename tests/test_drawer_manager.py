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


def test_apply_selected_heatmap():
    board = chess.Board("8/8/8/8/8/8/8/8 w - - 0 1")
    dm = DrawerManager()
    # provide fake heatmaps for testing
    dm.heatmaps = {
        "pawn": [[0.1] * 8 for _ in range(8)],
        "knight": [[0.2] * 8 for _ in range(8)],
    }

    dm.active_heatmap_piece = "knight"
    dm.collect_overlays({}, board)
    # value 0.2 -> r=51, g=204 => #33cc00
    assert ("gradient", "#33cc00") in dm.get_cell_overlays(0, 0)

    dm.active_heatmap_piece = None
    dm.collect_overlays({}, board)
    assert not dm.get_cell_overlays(0, 0)
