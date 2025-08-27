import json
import os
import tempfile

from analysis.loader import aggregate_run_stats, stream_runs


def _create_runs(tmpdir, count, moves_per_game=1):
    sample = {
        "moves": ["e4"] * moves_per_game,
        "fens": ["startpos"] * moves_per_game,
        "modules_w": ["m1"],
        "modules_b": ["m2"],
        "result": "1-0",
    }
    for i in range(count):
        with open(os.path.join(tmpdir, f"game{i}.json"), "w", encoding="utf-8") as fh:
            json.dump(sample, fh)


def test_stream_runs_sampling_deterministic():
    with tempfile.TemporaryDirectory() as tmpdir:
        _create_runs(tmpdir, 10)
        runs = list(stream_runs(tmpdir, sample_size=5, seed=1))
        runs2 = list(stream_runs(tmpdir, sample_size=5, seed=1))
        assert [r["game_id"] for r in runs] == [r["game_id"] for r in runs2]
        assert len(runs) == 5


def test_aggregate_run_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        _create_runs(tmpdir, 3, moves_per_game=2)
        stats = aggregate_run_stats(tmpdir)
        assert stats["games"] == 3
        assert stats["moves"] == 6
