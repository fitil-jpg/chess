import pytest

from scripts import tournament as T


def test_play_single_game_exceeds_max_plies_results_in_draw():
    # With max_plies=1, the loop stops after one move and game is a safety draw
    result = T.play_single_game("RandomBot", "RandomBot", max_plies=1)
    assert result == "1/2-1/2"
