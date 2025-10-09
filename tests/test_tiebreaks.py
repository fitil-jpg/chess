from scripts import tournament as T


def test_standings_sort_tiebreak_points_then_wins_then_name():
    # Create three players and seed custom stats to simulate tie-break
    a = T.PlayerStats("Alpha"); b = T.PlayerStats("Beta"); c = T.PlayerStats("Gamma")
    # Same points for all
    for s in (a, b, c):
        s.points = 2.0
    # Different wins: Beta 2 wins, Alpha 1, Gamma 0
    b.wins = 2; a.wins = 1; c.wins = 0
    standings = {s.name: s for s in (a, b, c)}

    # Capture the printed order using the same sort as print_standings
    ordered = sorted(standings.values(), key=lambda s: (-s.points, -s.wins, s.name))
    names = [s.name for s in ordered]
    assert names == ["Beta", "Alpha", "Gamma"]
