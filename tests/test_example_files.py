import csv
import json
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def test_queen_positions_csv():
    file_path = EXAMPLES_DIR / "queen_positions.csv"
    assert file_path.exists()

    with file_path.open() as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["square", "x", "y"]
        rows = list(reader)
        assert len(rows) == 2
        for row in rows:
            assert row["square"]
            int(row["x"])
            int(row["y"])


def test_agent_metrics_csv():
    file_path = EXAMPLES_DIR / "agent_metrics.csv"
    assert file_path.exists()

    with file_path.open() as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["agent", "wins", "losses", "draws"]
        rows = list(reader)
        assert len(rows) >= 1
        for row in rows:
            assert row["agent"]
            int(row["wins"])
            int(row["losses"])
            int(row["draws"])


def test_scenario_rules_json():
    file_path = EXAMPLES_DIR / "scenario_rules.json"
    assert file_path.exists()

    data = json.loads(file_path.read_text())
    assert isinstance(data, dict)
    assert "max_moves" in data and isinstance(data["max_moves"], int)
    assert "allow_castling" in data and isinstance(data["allow_castling"], bool)
    assert "time_control" in data and isinstance(data["time_control"], str)
