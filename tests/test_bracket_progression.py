from scripts import tournament as T


def test_round_robin_4_agents_progresses_and_populates_standings():
    agents = ["RandomBot", "FortifyBot", "AggressiveBot", "EndgameBot"]
    standings = T.run_round_robin(agents, games_per_pair=1, max_plies=2)
    # All four present in standings
    assert set(standings.keys()) == set(agents)
    # Each player plays 3 games in RR with 4 players
    for s in standings.values():
        assert s.played == 3
        # points should be in [0,3] with 0.5 increments
        assert 0.0 <= s.points <= 3.0
