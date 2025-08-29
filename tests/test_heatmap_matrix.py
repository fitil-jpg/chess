import csv
import struct
import zlib
import types

import analysis.loader as loader


def _build_matrix(records, piece):
    """Return an 8x8 matrix counting occurrences of *piece* in records."""
    matrix = [[0 for _ in range(8)] for _ in range(8)]
    for rec in records:
        if rec["piece"] != piece:
            continue
        file_idx = ord(rec["to"][0]) - ord("a")
        rank_idx = int(rec["to"][1]) - 1
        matrix[7 - rank_idx][file_idx] += 1
    return matrix


def _save_png(path, matrix):
    """Write *matrix* as a grayscale PNG without external deps."""
    height = len(matrix)
    width = len(matrix[0]) if height else 0
    maxval = max((max(row) for row in matrix), default=1)
    raw = b"".join(
        b"\x00" + bytes(int(255 * val / maxval) for val in row) for row in matrix
    )
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
        fh.write(struct.pack(">I", len(ihdr)))
        fh.write(b"IHDR")
        fh.write(ihdr)
        fh.write(struct.pack(">I", zlib.crc32(b"IHDR" + ihdr)))
        compressed = zlib.compress(raw)
        fh.write(struct.pack(">I", len(compressed)))
        fh.write(b"IDAT")
        fh.write(compressed)
        fh.write(struct.pack(">I", zlib.crc32(b"IDAT" + compressed)))
        fh.write(struct.pack(">I", 0))
        fh.write(b"IEND")
        fh.write(struct.pack(">I", zlib.crc32(b"IEND")))


def _minimal_chess_module():
    Piece = types.SimpleNamespace

    def piece_name(symbol):
        mapping = {
            "p": "pawn",
            "n": "knight",
            "b": "bishop",
            "r": "rook",
            "q": "queen",
            "k": "king",
        }
        return mapping[symbol.lower()]

    def square_name(square: int) -> str:
        files = "abcdefgh"
        return files[square % 8] + str(square // 8 + 1)

    class Board:
        def __init__(self, fen: str):
            board_part = fen.split()[0]
            self._map = {}
            rows = board_part.split("/")
            for r, row in enumerate(reversed(rows)):
                file = 0
                for ch in row:
                    if ch.isdigit():
                        file += int(ch)
                    else:
                        sq = r * 8 + file
                        self._map[sq] = Piece(piece_type=ch)
                        file += 1

        def piece_map(self):
            return self._map

    module = types.SimpleNamespace(Board=Board, piece_name=piece_name, square_name=square_name)
    return module


def test_heatmap_matrix(tmp_path, monkeypatch):
    # Patch loader.chess with minimal implementation
    monkeypatch.setattr(loader, "chess", _minimal_chess_module())

    fens = [
        "8/8/8/8/8/8/8/Q7 w - - 0 1",
        "8/8/8/8/8/8/8/1Q6 w - - 0 1",
        "8/8/8/8/8/8/8/2Q5 w - - 0 1",
    ]

    csv_path = tmp_path / "fens.csv"
    records = loader.export_fen_table(fens, csv_path=str(csv_path))
    assert csv_path.is_file()

    matrix = _build_matrix(records, "queen")
    assert len(matrix) == 8 and all(len(row) == 8 for row in matrix)
    # Queens placed on a1, b1 and c1
    assert matrix[7][0] == 1
    assert matrix[7][1] == 1
    assert matrix[7][2] == 1
    assert sum(sum(row) for row in matrix) == 3

    matrix_csv = tmp_path / "queen_matrix.csv"
    with matrix_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerows(matrix)
    assert matrix_csv.is_file() and matrix_csv.stat().st_size > 0

    png_path = tmp_path / "queen_heatmap.png"
    _save_png(png_path, matrix)
    assert png_path.is_file() and png_path.stat().st_size > 0
