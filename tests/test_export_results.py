import csv
import json

from analysis.loader import export_agent_metrics, export_scenarios


def test_export_agent_metrics(tmp_path):
    metrics = {"strength": 0.5, "mobility": 3.2}
    csv_file = tmp_path / "metrics.csv"
    json_file = tmp_path / "metrics.json"
    result = export_agent_metrics(
        metrics, csv_path=str(csv_file), json_path=str(json_file)
    )

    assert result == metrics
    assert csv_file.exists() and json_file.exists()

    with open(csv_file, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(metrics)
    assert any(row["metric"] == "strength" for row in rows)

    with open(json_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data == metrics


def test_export_scenarios(tmp_path):
    fens = ["8/3q1r2/8/4N3/8/8/8/8 w - - 0 1"]
    csv_file = tmp_path / "scenarios.csv"
    json_file = tmp_path / "scenarios.json"
    records = export_scenarios(
        fens, csv_path=str(csv_file), json_path=str(json_file)
    )

    assert records
    assert csv_file.exists() and json_file.exists()

    with open(csv_file, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert any(row["id"] == "knight_fork" and row["square"] == "e5" for row in rows)

    with open(json_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert any(d["id"] == "knight_fork" and d["square"] == "e5" for d in data)

