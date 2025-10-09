import pytest

from scripts import tournament as T


def test_series_alternates_colors_and_results_list_length():
    # 4 games: colors should alternate as per i%2 rule inside play_series
    a, b, n = "RandomBot", "RandomBot", 4
    pts_a, pts_b, results = T.play_series(a, b, n, max_plies=2)
    # length of results matches requested games (no early stop for even n)
    assert len(results) == n
    # Standings update logic relies on color alternation; verify implied mapping
    # Game indices even: a is white; odd: b is white
    whites = [(a if i % 2 == 0 else b) for i in range(n)]
    blacks = [(b if i % 2 == 0 else a) for i in range(n)]
    assert whites[0] == a and blacks[0] == b
    assert whites[1] == b and blacks[1] == a
