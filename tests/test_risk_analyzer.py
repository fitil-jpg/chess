import chess

from chess_ai.risk_analyzer import RiskAnalyzer
from chess_ai.decision_engine import DecisionEngine
from chess_ai.chess_bot import ChessBot


def test_risk_analyzer_detects_hanging_piece():
    board = chess.Board("4k3/8/8/1pn5/8/1P6/8/3QK3 w - - 0 1")
    analyzer = RiskAnalyzer()
    risky_move = chess.Move.from_uci("d1a4")
    safe_move = chess.Move.from_uci("d1e2")
    assert analyzer.is_risky(board, risky_move)
    assert not analyzer.is_risky(board, safe_move)


def test_risk_analyzer_handles_hanging_and_safe_moves():
    board = chess.Board("r3k2r/2n5/8/8/8/8/8/R3K2R w KQkq - 0 1")
    analyzer = RiskAnalyzer()
    risky = chess.Move.from_uci("a1a8")
    safe = chess.Move.from_uci("h1h8")
    assert analyzer.is_risky(board, risky)
    assert not analyzer.is_risky(board, safe)


def test_alpha_beta_prunes(monkeypatch):
    board = chess.Board()
    analyzer = RiskAnalyzer()
    m1 = chess.Move.from_uci("e2e4")
    m2 = chess.Move.from_uci("d2d4")

    def fake_legal_moves(self):
        # Only expose the two test moves at the root; no moves after one is made.
        return [m1, m2] if not self.move_stack else []

    monkeypatch.setattr(chess.Board, "legal_moves", property(fake_legal_moves))
    original_push = board.push

    def fake_push(move):
        if move == m2:
            raise AssertionError("alpha-beta failed to prune")
        return original_push(move)

    board.push = fake_push

    result = analyzer._search(board, 1, True, board.turn, alpha=-float("inf"), beta=0)
    assert result == 0


def test_decision_engine_avoids_risky_trap(monkeypatch):
    board = chess.Board("r2q2k1/8/8/3B2B1/8/8/8/4K3 w - - 0 1")
    trap = chess.Move.from_uci("g5d8")
    safe = chess.Move.from_uci("d5a8")

    def fake_is_risky(self, b, m):
        return m == trap

    monkeypatch.setattr(RiskAnalyzer, "is_risky", fake_is_risky)
    engine = DecisionEngine()
    best = engine.choose_best_move(board)
    assert best == safe


def test_chess_bot_avoids_risky_trap(monkeypatch, context, evaluator):
    board = chess.Board("r2q2k1/8/8/3B2B1/8/8/8/4K3 w - - 0 1")
    trap = chess.Move.from_uci("g5d8")
    safe = chess.Move.from_uci("d5a8")

    def fake_is_risky(self, b, m):
        return m == trap

    monkeypatch.setattr(RiskAnalyzer, "is_risky", fake_is_risky)
    bot = ChessBot(chess.WHITE)
    evaluator.board = board
    move, conf = bot.choose_move(board, context=context, evaluator=evaluator)
    assert move == safe

