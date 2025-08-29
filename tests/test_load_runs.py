import importlib.util
import json
import os
import tempfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "_load_runs", Path(__file__).resolve().parents[1] / "utils" / "load_runs.py"
)
load_runs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(load_runs_module)
load_runs = load_runs_module.load_runs


def test_load_runs_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample = {
            "moves": ["e4"],
            "fens": ["startpos"],
            "modules_w": ["module1"],
            "modules_b": ["module2"],
            "result": "1-0",
        }
        with open(os.path.join(tmpdir, "game1.json"), "w", encoding="utf-8") as f:
            json.dump(sample, f)

        runs = load_runs(tmpdir)
        assert isinstance(runs, list)
        assert len(runs) == 1
        run = runs[0]
        assert isinstance(run, dict)
        assert run["game_id"] == "game1"
        assert run["moves"] == sample["moves"]
        assert run["fens"] == sample["fens"]
        assert run["modules_w"] == sample["modules_w"]
        assert run["modules_b"] == sample["modules_b"]


def test_load_runs_missing_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        incomplete = {
            "moves": [],
            "fens": [],
            "modules_w": [],
        }
        with open(os.path.join(tmpdir, "game2.json"), "w", encoding="utf-8") as f:
            json.dump(incomplete, f)

        try:
            load_runs(tmpdir)
            assert False, "Expected ValueError due to missing keys"
        except ValueError as e:
            msg = str(e)
            assert "modules_b" in msg and "result" not in msg


def test_load_runs_missing_result_defaults_star():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample = {
            "moves": [],
            "fens": [],
            "modules_w": [],
            "modules_b": [],
        }
        with open(os.path.join(tmpdir, "game3.json"), "w", encoding="utf-8") as f:
            json.dump(sample, f)

        runs = load_runs(tmpdir)
        assert len(runs) == 1
        assert runs[0]["result"] == "*"


def test_load_runs_missing_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        missing = os.path.join(tmpdir, "missing")
        with pytest.raises(FileNotFoundError):
            load_runs(missing)


def test_filter_by_player_color_and_phase():
    with tempfile.TemporaryDirectory() as tmpdir:
        fen_opening = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        fen_middle = "rnbqkbnr/8/8/8/8/8/8/RNBQKBNR b KQkq - 0 1"

        sample = {
            "moves": ["e4", "e5"],
            "fens": [fen_opening, fen_middle],
            "modules_w": ["module1"],
            "modules_b": ["module2"],
        }
        with open(os.path.join(tmpdir, "game.json"), "w", encoding="utf-8") as f:
            json.dump(sample, f)

        run = load_runs(tmpdir)[0]

        white_fens = [
            fen for fen in run["fens"] if fen.split()[1] == "w"
        ]
        black_fens = [
            fen for fen in run["fens"] if fen.split()[1] == "b"
        ]
        assert white_fens == [fen_opening]
        assert black_fens == [fen_middle]

        def classify(fen: str) -> str:
            pieces = sum(ch.isalpha() for ch in fen.split()[0])
            if pieces > 20:
                return "opening"
            if pieces > 10:
                return "middlegame"
            return "endgame"

        openings = [fen for fen in run["fens"] if classify(fen) == "opening"]
        middles = [fen for fen in run["fens"] if classify(fen) == "middlegame"]
        assert openings == [fen_opening]
        assert middles == [fen_middle]


if __name__ == "__main__":
    test_load_runs_valid()
    test_load_runs_missing_key()
