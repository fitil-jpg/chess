import chess
import pytest

from metrics.attack_map import attack_count_per_square, AttackMapCache


def test_attack_count_per_square_matches_board_attackers():
    board = chess.Board()
    result = attack_count_per_square(board)

    assert set(result.keys()) == {chess.WHITE, chess.BLACK}
    assert len(result[chess.WHITE]) == 64
    assert len(result[chess.BLACK]) == 64

    for sq in chess.SQUARES:
        assert result[chess.WHITE][sq] == len(board.attackers(chess.WHITE, sq))
        assert result[chess.BLACK][sq] == len(board.attackers(chess.BLACK, sq))


def test_attack_counts_change_after_move():
    board = chess.Board()
    before = attack_count_per_square(board)
    board.push_san("e4")
    after = attack_count_per_square(board)

    # Ensure at least one square's counts differ after a move
    changed = any(
        before[chess.WHITE][sq] != after[chess.WHITE][sq]
        or before[chess.BLACK][sq] != after[chess.BLACK][sq]
        for sq in chess.SQUARES
    )
    assert changed


def test_attack_map_cache_basic_usage():
    board = chess.Board()
    cache = AttackMapCache(maxsize=2)
    first = cache.get(board)
    second = cache.get(board)

    # Identical results for the same position
    assert first == second

    board.push_san("e4")
    third = cache.get(board)
    assert third != first  # position changed, so counts should change
