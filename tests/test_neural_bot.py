import chess

from chess_ai.neural_bot import NeuralBot
from chess_ai.dynamic_bot import DynamicBot


class FakeNet:
    def predict_many(self, boards):
        policy = {
            chess.Move.from_uci("e2e4"): 0.7,
            chess.Move.from_uci("d2d4"): 0.3,
        }
        return [(policy, 0.5) for _ in boards]


def test_neural_bot_converts_network_output(context, evaluator):
    board = chess.Board()
    bot = NeuralBot(chess.WHITE, net=FakeNet())
    move, conf = bot.choose_move(board, context=context, evaluator=evaluator)
    assert move == chess.Move.from_uci("e2e4")
    assert conf == 0.5


def test_dynamic_bot_registers_neural_bot():
    bot = DynamicBot(chess.WHITE, weights={"neural": 0.25})
    assert any(
        isinstance(agent, NeuralBot) and weight == 0.25
        for agent, weight in bot.agents
    )
