from scenarios import detect_scenarios


def test_isolated_pawn():
    scenarios = detect_scenarios("8/8/8/8/3P4/8/8/8 w - - 0 1")
    assert any(s["id"] == "isolated_pawn" and s["square"] == "d4" for s in scenarios)


def test_knight_fork():
    scenarios = detect_scenarios("8/3q1r2/8/4N3/8/8/8/8 w - - 0 1")
    assert any(s["id"] == "knight_fork" and s["square"] == "e5" for s in scenarios)


def test_no_scenarios_on_startpos():
    scenarios = detect_scenarios("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    assert scenarios == []
