import textwrap

import chess

from analysis.pgn_loader import stream_pgn_games


def _sample_pgn() -> str:
    return textwrap.dedent(
        """
        [Event "Test"]
        [White "Alice"]
        [Black "Bob"]
        [Result "*"]

        1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 *
        """
    ).strip()


def test_stream_pgn_games_basic(tmp_path):
    pgn_path = tmp_path / "game.pgn"
    pgn_path.write_text(_sample_pgn(), encoding="utf-8")

    games = list(stream_pgn_games(str(pgn_path)))
    assert len(games) == 1
    game = games[0]
    assert game["metadata"]["White"] == "Alice"
    assert game["moves"] == [
        "e2e4",
        "e7e5",
        "g1f3",
        "b8c6",
        "f1b5",
        "a7a6",
    ]
    assert len(game["fens"]) == len(game["moves"])

    board = chess.Board()
    for fen, mv in zip(game["fens"], game["moves"]):
        assert fen == board.fen()
        board.push_uci(mv)


def test_stream_pgn_games_filters(tmp_path):
    pgn_path = tmp_path / "game.pgn"
    pgn_path.write_text(_sample_pgn(), encoding="utf-8")

    game = next(stream_pgn_games(str(pgn_path), move=2))
    assert game["moves"] == ["g1f3", "b8c6"]

    game = next(stream_pgn_games(str(pgn_path), player=chess.WHITE))
    assert game["moves"] == ["e2e4", "g1f3", "f1b5"]

    games = list(stream_pgn_games(str(pgn_path), phase="opening"))
    assert len(games[0]["moves"]) == 6

    assert list(stream_pgn_games(str(pgn_path), phase="endgame")) == []
