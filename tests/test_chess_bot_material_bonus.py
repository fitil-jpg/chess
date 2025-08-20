import chess

from chess_ai.chess_bot import ChessBot, MATERIAL_DEFICIT_BONUS
from utils import GameContext


def test_chess_bot_material_deficit_capture_bonus(context):
    # White pawn on d4 captures a pawn on e5.  When behind in material the
    # bot should receive an additional bonus for such capturing moves.
    board = chess.Board("8/8/8/4p3/3P4/8/8/4K3 w - - 0 1")
    bot = ChessBot(chess.WHITE)
    move = chess.Move.from_uci("d4e5")

    score_even, _ = bot.evaluate_move(
        board, move, context
    )
    score_behind, _ = bot.evaluate_move(
        board, move, GameContext(material_diff=-2)
    )

    assert score_behind - score_even == 2 * MATERIAL_DEFICIT_BONUS
