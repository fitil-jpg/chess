from analysis.generate_heatmaps_from_wins import generate_heatmaps_from_wins
from analysis.pgn_loader import stream_pgn_games


def test_generate_heatmaps_from_wins_filters_results(monkeypatch, tmp_path):
    pgn_text = """
[Event "WinGame"]
[Site "?"]
[Date "2024.01.01"]
[Round "1"]
[White "White A"]
[Black "Black A"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0

[Event "DrawGame"]
[Site "?"]
[Date "2024.01.02"]
[Round "1"]
[White "White B"]
[Black "Black B"]
[Result "1/2-1/2"]

1. d4 d5 2. c4 c6 1/2-1/2

[Event "LoseGame"]
[Site "?"]
[Date "2024.01.03"]
[Round "1"]
[White "White C"]
[Black "Black C"]
[Result "0-1"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 0-1
"""
    pgn_path = tmp_path / "games.pgn"
    pgn_path.write_text(pgn_text.strip() + "\n", encoding="utf-8")

    captured = {}

    def fake_generate_heatmaps(fens, *, out_dir, pattern_set, use_wolfram):
        captured["fens"] = list(fens)
        captured["out_dir"] = out_dir
        captured["pattern_set"] = pattern_set
        captured["use_wolfram"] = use_wolfram
        return {pattern_set: {"status": "ok"}}

    monkeypatch.setattr(
        "analysis.generate_heatmaps_from_wins.generate_heatmaps",
        fake_generate_heatmaps,
    )

    result = generate_heatmaps_from_wins(
        str(pgn_path), out_dir="custom", pattern_set="default", use_wolfram=True
    )
    assert result == {"default": {"status": "ok"}}

    winning_games = [
        game
        for game in stream_pgn_games(str(pgn_path))
        if game["metadata"].get("Result") in {"1-0", "0-1"}
    ]
    expected_fens = [fen for game in winning_games for fen in game["fens"]]

    assert captured["fens"] == expected_fens
    assert captured["out_dir"] == "custom"
    assert captured["pattern_set"] == "default"
    assert captured["use_wolfram"] is True


def test_generate_heatmaps_from_wins_returns_empty_when_no_wins(monkeypatch, tmp_path):
    pgn_text = """
[Event "DrawGame"]
[Site "?"]
[Date "2024.02.01"]
[Round "1"]
[White "White A"]
[Black "Black A"]
[Result "1/2-1/2"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1/2-1/2
"""
    pgn_path = tmp_path / "draws_only.pgn"
    pgn_path.write_text(pgn_text.strip() + "\n", encoding="utf-8")

    def fail_generate_heatmaps(*args, **kwargs):  # pragma: no cover - should not run
        raise AssertionError("generate_heatmaps should not be called when there are no wins")

    monkeypatch.setattr(
        "analysis.generate_heatmaps_from_wins.generate_heatmaps",
        fail_generate_heatmaps,
    )

    result = generate_heatmaps_from_wins(str(pgn_path))

    assert result == {}
