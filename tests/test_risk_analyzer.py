import chess

from chess_ai.risk_analyzer import RiskAnalyzer
from chess_ai.decision_engine import DecisionEngine
from chess_ai.chess_bot import ChessBot
from core.evaluator import Evaluator


def test_risk_analyzer_detects_hanging_piece():
    board = chess.Board("4k3/8/8/1p6/8/8/8/3QK3 w - - 0 1")
    analyzer = RiskAnalyzer()
    risky_move = chess.Move.from_uci("d1a4")
    safe_move = chess.Move.from_uci("d1e2")
    assert analyzer.is_risky(board, risky_move)
    assert not analyzer.is_risky(board, safe_move)


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


def test_chess_bot_avoids_risky_trap(monkeypatch):
    board = chess.Board("r2q2k1/8/8/3B2B1/8/8/8/4K3 w - - 0 1")
    trap = chess.Move.from_uci("g5d8")
    safe = chess.Move.from_uci("d5a8")

    def fake_is_risky(self, b, m):
        return m == trap

    monkeypatch.setattr(RiskAnalyzer, "is_risky", fake_is_risky)
    bot = ChessBot(chess.WHITE)
    evaluator = Evaluator(board)
    move, conf = bot.choose_move(board, evaluator)
    assert move == safe

