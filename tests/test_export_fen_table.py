import csv

from analysis.loader import export_fen_table


def test_export_fen_table(tmp_path):
    fens = [
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    ]
    csv_file = tmp_path / "fens.csv"
    records = export_fen_table(fens, csv_path=str(csv_file))

    # 32 pieces in the starting position plus header line in CSV
    assert csv_file.exists()
    with open(csv_file, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 32

    # Ensure at least one known piece/square entry exists
    assert any(r["piece"] == "king" and r["to"] == "e1" for r in records)
