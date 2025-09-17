import csv
import json
import textwrap
from pathlib import Path

import chess
from analysis.pgn_loader import stream_pgn_games
from analysis.loader import export_fen_table, export_agent_metrics, export_scenarios
from utils import integration


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


def test_full_pipeline(tmp_path, monkeypatch):
    # --- PGN to FENs -----------------------------------------------------
    pgn_path = tmp_path / "game.pgn"
    pgn_path.write_text(_sample_pgn(), encoding="utf-8")
    game = next(stream_pgn_games(str(pgn_path)))
    fens = list(game["fens"])
    # Add a FEN that triggers a scenario to ensure output
    fens.append("8/3q1r2/8/4N3/8/8/8/8 w - - 0 1")

    # --- Export FEN table ------------------------------------------------
    fen_csv = tmp_path / "fens.csv"
    export_fen_table(fens, csv_path=str(fen_csv))
    assert fen_csv.exists()
    with open(fen_csv, newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == ["fen_id", "piece", "to"]

    # --- Heatmap generation (stubbed Rscript) ---------------------------
    heat_dir = tmp_path / "heatmaps"

    def fake_run(cmd, check):
        out_dir = Path(cmd[-1]).parent
        # generate one dummy heatmap file
        hm = out_dir / "heatmap_0.json"
        hm.write_text(json.dumps([[0] * 8 for _ in range(8)]), encoding="utf-8")
        return types.SimpleNamespace(returncode=0)

    import types

    monkeypatch.setattr(integration.subprocess, "run", fake_run)
    heatmaps = integration.generate_heatmaps(fens, out_dir=str(heat_dir))
    default_dir = heat_dir / "default"
    assert (default_dir / "heatmap_0.json").exists()
    assert "default" in heatmaps
    assert "0" in heatmaps["default"] and len(heatmaps["default"]["0"]) == 8

    # --- Metrics ---------------------------------------------------------
    metrics = integration.compute_metrics(fens[0])
    flat_metrics = {**metrics["short_term"], **metrics["long_term"]}
    metrics_csv = tmp_path / "metrics.csv"
    metrics_json = tmp_path / "metrics.json"
    export_agent_metrics(flat_metrics, csv_path=str(metrics_csv), json_path=str(metrics_json))
    assert metrics_csv.exists() and metrics_json.exists()
    with open(metrics_json, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert "attacked_squares" in data

    # --- Scenarios -------------------------------------------------------
    scenarios_csv = tmp_path / "scenarios.csv"
    scenarios_json = tmp_path / "scenarios.json"
    records = export_scenarios(fens, csv_path=str(scenarios_csv), json_path=str(scenarios_json))
    assert records
    assert scenarios_csv.exists() and scenarios_json.exists()
    with open(scenarios_json, "r", encoding="utf-8") as fh:
        scenario_data = json.load(fh)
    assert all("id" in sc and "fen_id" in sc for sc in scenario_data)
