import json
from analysis.loader import aggregate_stats


def _write_run(path, name, moves, modules_w, modules_b):
    data = {
        "moves": moves,
        "fens": [" "] * len(moves),
        "modules_w": modules_w,
        "modules_b": modules_b,
    }
    (path / f"{name}.json").write_text(json.dumps(data))


def test_aggregate_stats_sampling(tmp_path):
    _write_run(tmp_path, "g1", ["e2e4"], ["A"], [])
    _write_run(tmp_path, "g2", ["e2e4", "e7e5"], ["B"], ["C"])
    _write_run(tmp_path, "g3", ["d2d4"], ["A"], ["B"])

    stats = aggregate_stats(tmp_path, limit=2)
    assert stats["games"] == 2
    assert stats["moves"] == 3
    assert stats["module_usage"] == {"A": 1, "B": 1, "C": 1}

    stats1 = aggregate_stats(tmp_path, limit=2, seed=0)
    stats2 = aggregate_stats(tmp_path, limit=2, seed=0)
    assert stats1 == stats2
