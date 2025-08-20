from vendors import setup_path  # noqa: F401

import json
import os
import tempfile
from utils.load_runs import load_runs


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
        assert len(runs) == 1
        run = runs[0]
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


if __name__ == "__main__":
    test_load_runs_valid()
    test_load_runs_missing_key()
