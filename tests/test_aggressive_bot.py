import chess
from chess_ai.aggressive_bot import AggressiveBot
from utils import GameContext


class DummyEvaluator:
    def position_score(self, board, color):
        return 0


def test_capture_gain_scaled_when_behind(capfd):
    board = chess.Board("8/8/8/3r4/2P5/8/8/8 w - - 0 1")
    ctx = GameContext(material_diff=-1, mobility=0, king_safety=0)
    bot = AggressiveBot(chess.WHITE, capture_gain_factor=1.5)
    move, score = bot.choose_move(board, context=ctx, evaluator=DummyEvaluator(), debug=True)
    assert move == chess.Move.from_uci("c4d5")
    assert score == 6.0
    output = capfd.readouterr().out
    assert "material deficit" in output
