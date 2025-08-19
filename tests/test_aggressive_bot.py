import chess
from chess_ai.aggressive_bot import AggressiveBot
from utils import GameContext


def test_capture_gain_scaled_when_behind(capfd, evaluator):
    board = chess.Board("8/8/8/3r4/2P5/8/8/8 w - - 0 1")
    evaluator.board = board
    ctx = GameContext(material_diff=-1, mobility=0, king_safety=0)
    bot = AggressiveBot(chess.WHITE, capture_gain_factor=1.5)
    move, score = bot.choose_move(board, context=ctx, evaluator=evaluator, debug=True)
    assert move == chess.Move.from_uci("c4d5")

    tmp = board.copy(stack=False)
    tmp.push(chess.Move.from_uci("c4d5"))
    expected = 6 + evaluator.position_score(tmp, chess.WHITE)
    assert score == expected

    output = capfd.readouterr().out
    assert "material deficit" in output
