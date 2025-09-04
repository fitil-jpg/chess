import pytest

chess = pytest.importorskip("chess")
if not hasattr(chess, "Board"):
    pytest.skip("python-chess not installed", allow_module_level=True)

from core.evaluator import is_piece_mated


def test_is_piece_mated_detects_trapped_piece():
    board = chess.Board("n5k1/1B6/8/P7/8/8/2R5/7K w - - 0 1")
    # The knight on a8 is attacked by the bishop on b7.  Its only legal moves
    # (b6 and c7) are also unsafe because they are attacked by the pawn on a5
    # and the rook on c2 respectively, so the piece is considered mated.
    assert is_piece_mated(board, chess.A8)
    board.push(chess.Move.from_uci("c2c7"))
    # Advancing the rook to c7 allows the knight to capture it and land on a
    # safe square, meaning the piece is no longer mated.
    assert not is_piece_mated(board, chess.A8)


def test_is_piece_mated_false_when_escape_exists():
    board = chess.Board("n5k1/1B6/8/8/8/8/8/7K w - - 0 1")
    assert not is_piece_mated(board, chess.A8)
