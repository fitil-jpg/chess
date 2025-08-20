import chess
import core.piece as piece
import core.board_analyzer as ba


def test_get_all_attacks_builds_board_once(monkeypatch):
    base = chess.Board()
    base.clear()
    base.set_piece_at(chess.D4, chess.Piece(chess.ROOK, chess.WHITE))
    board = piece._build_board(base)
    analyzer = ba.BoardAnalyzer(board)

    calls = {'n': 0}
    original = ba.build_chess_board

    def wrapper(b):
        calls['n'] += 1
        return original(b)

    monkeypatch.setattr(ba, 'build_chess_board', wrapper)
    attacks = analyzer.get_all_attacks('white')
    assert attacks == set(base.attacks(chess.D4))
    assert calls['n'] == 1


def test_get_defense_map_builds_board_once(monkeypatch):
    base = chess.Board("k7/8/3P4/8/3R4/8/8/K7 w - - 0 1")
    board = piece._build_board(base)
    analyzer = ba.BoardAnalyzer(board)

    calls = {'n': 0}
    original = ba.build_chess_board

    def wrapper(b):
        calls['n'] += 1
        return original(b)

    monkeypatch.setattr(ba, 'build_chess_board', wrapper)
    defense_map = analyzer.get_defense_map()
    assert defense_map['white'] == {chess.D6}
    assert defense_map['black'] == set()
    assert calls['n'] == 1
