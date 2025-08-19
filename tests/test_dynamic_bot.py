import chess
import pytest

from chess_ai.dynamic_bot import DynamicBot


def test_meta_agent_combines_weighted_subbots(context, evaluator):
    board = chess.Board()
    evaluator.board = board

    bot = DynamicBot(chess.WHITE)
    bot.agents = []

    class BotA:
        def choose_move(self, board, context=None, evaluator=None, debug=False):
            return chess.Move.from_uci("e2e4"), 0.6

    class BotB:
        def choose_move(self, board, context=None, evaluator=None, debug=False):
            return chess.Move.from_uci("e2e4"), 0.4

    bot.register_agent(BotA(), weight=2.0)
    bot.register_agent(BotB(), weight=0.5)

    move, score = bot.choose_move(board, context=context, evaluator=evaluator)
    assert move == chess.Move.from_uci("e2e4")
    assert score == pytest.approx(0.6 * 2.0 + 0.4 * 0.5)
