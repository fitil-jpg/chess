import pytest
import chess

from chess_ai import fortify_bot
from chess_ai.fortify_bot import FortifyBot
from core.constants import KING_SAFETY_THRESHOLD


class DummyEval:
    def __init__(self):
        self.calls = 0

    def position_score(self, board, color):
        self.calls += 1
        return 0


def test_skips_when_king_safe(capfd, context, evaluator):
    board = chess.Board()
    evaluator.board = board
    bot = FortifyBot(chess.WHITE)
    context.king_safety = KING_SAFETY_THRESHOLD
    move, score = bot.choose_move(board, context=context, evaluator=evaluator, debug=True)
    assert move is None and score == 0.0
    out = capfd.readouterr().out
    assert "king safety" in out


def test_reuses_provided_evaluator(monkeypatch, context):
    board = chess.Board()
    bot = FortifyBot(chess.WHITE)
    context.king_safety = -1
    dummy = DummyEval()

    def boom(*args, **kwargs):
        raise AssertionError("Evaluator should not be created")

    monkeypatch.setattr(fortify_bot, "Evaluator", boom)
    fortify_bot._SHARED_EVALUATOR = None

    move, score = bot.choose_move(board, context=context, evaluator=dummy)
    assert dummy.calls > 0
