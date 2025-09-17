import pytest

chess = pytest.importorskip("chess")

from ui.drawer_manager import DrawerManager


def test_set_heatmap_set_updates_overlays_and_piece():
    manager = DrawerManager()
    manager.heatmap_sets = {
        "default": {"pawn": [[0.0 for _ in range(8)] for _ in range(8)]},
        "aggressive": {"pawn": [[1.0 for _ in range(8)] for _ in range(8)]},
    }
    assert manager.list_heatmap_sets() == ["aggressive", "default"]

    manager.active_heatmap_set = "default"
    manager.heatmaps = manager.heatmap_sets["default"]
    manager.active_heatmap_piece = "pawn"

    manager.collect_overlays({}, chess.Board())
    before = manager.get_cell_overlays(0, 0)
    assert before and before[0][0] == "gradient"

    manager.set_heatmap_set("aggressive")

    after = manager.get_cell_overlays(0, 0)
    assert manager.active_heatmap_set == "aggressive"
    assert manager.active_heatmap_piece == "pawn"
    assert after and after[0][0] == "gradient"
    assert after[0][1] != before[0][1]
