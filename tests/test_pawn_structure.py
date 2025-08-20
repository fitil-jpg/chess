import chess
from core.evaluator import Evaluator


def _is_isolated(board: chess.Board, square: int, files: dict[int, list[int]]) -> bool:
    file = chess.square_file(square)
    for adj in (file - 1, file + 1):
        if 0 <= adj < 8 and files.get(adj):
            return False
    return True


def _is_doubled(files: dict[int, list[int]], square: int) -> bool:
    file = chess.square_file(square)
    return len(files.get(file, [])) > 1


def test_is_isolated():
    board = chess.Board("8/8/8/8/2P5/8/8/8 w - - 0 1")
    pawns = [sq for sq, p in board.piece_map().items() if p.piece_type == chess.PAWN and p.color == chess.WHITE]
    files: dict[int, list[int]] = {}
    for sq in pawns:
        files.setdefault(chess.square_file(sq), []).append(sq)
    assert _is_isolated(board, chess.C4, files)

    board = chess.Board("8/8/8/8/2P5/8/1P6/8 w - - 0 1")
    pawns = [sq for sq, p in board.piece_map().items() if p.piece_type == chess.PAWN and p.color == chess.WHITE]
    files = {}
    for sq in pawns:
        files.setdefault(chess.square_file(sq), []).append(sq)
    assert not _is_isolated(board, chess.C4, files)


def test_is_doubled():
    board = chess.Board("8/8/8/8/2P5/2P5/8/8 w - - 0 1")
    pawns = [sq for sq, p in board.piece_map().items() if p.piece_type == chess.PAWN and p.color == chess.WHITE]
    files: dict[int, list[int]] = {}
    for sq in pawns:
        files.setdefault(chess.square_file(sq), []).append(sq)
    assert _is_doubled(files, chess.C4)

    board = chess.Board("8/8/8/8/2P5/8/8/8 w - - 0 1")
    pawns = [sq for sq, p in board.piece_map().items() if p.piece_type == chess.PAWN and p.color == chess.WHITE]
    files = {}
    for sq in pawns:
        files.setdefault(chess.square_file(sq), []).append(sq)
    assert not _is_doubled(files, chess.C4)


def test_is_passed():
    board = chess.Board("8/8/8/8/2P5/8/8/8 w - - 0 1")
    evaluator = Evaluator(board)
    assert evaluator._is_passed_pawn(chess.C4, chess.WHITE, [])

    board = chess.Board("8/8/2p5/8/2P5/8/8/8 w - - 0 1")
    evaluator = Evaluator(board)
    enemy = [chess.C6]
    assert not evaluator._is_passed_pawn(chess.C4, chess.WHITE, enemy)


def test_pawn_structure_score_isolated_white():
    board = chess.Board("8/8/2pp4/8/2P5/8/8/8 w - - 0 1")
    evaluator = Evaluator(board)
    assert evaluator.pawn_structure_score() == -10


def test_pawn_structure_score_isolated_black():
    board = chess.Board("8/8/8/2p5/1PP5/8/8/8 w - - 0 1")
    evaluator = Evaluator(board)
    assert evaluator.pawn_structure_score() == 10


def test_pawn_structure_score_doubled_white():
    board = chess.Board("8/8/2pp4/8/2P5/1PP5/8/8 w - - 0 1")
    evaluator = Evaluator(board)
    assert evaluator.pawn_structure_score() == -5


def test_pawn_structure_score_doubled_black():
    board = chess.Board("8/8/1pp5/2p5/8/1PP5/8/8 w - - 0 1")
    evaluator = Evaluator(board)
    assert evaluator.pawn_structure_score() == 5


def test_pawn_structure_score_passed_white():
    blocked = chess.Board("8/8/2pp4/8/2P5/8/8/8 w - - 0 1")
    passed = chess.Board("8/8/8/8/2P5/8/8/8 w - - 0 1")
    ev_blocked = Evaluator(blocked)
    ev_passed = Evaluator(passed)
    assert ev_passed.pawn_structure_score() - ev_blocked.pawn_structure_score() == ev_passed.passed_bonus


def test_pawn_structure_score_passed_black():
    blocked = chess.Board("8/8/8/2p5/1PP5/8/8/8 w - - 0 1")
    passed = chess.Board("8/8/8/2p5/8/8/8/8 w - - 0 1")
    ev_blocked = Evaluator(blocked)
    ev_passed = Evaluator(passed)
    assert ev_passed.pawn_structure_score() - ev_blocked.pawn_structure_score() == -ev_passed.passed_bonus

