import random
import chess

from chess_ai.endgame_bot import EndgameBot
from utils import GameContext


def test_check_bonus_scaled_by_material(context):
    # Position after 1.e4 f6 where Qh5 delivers check on e8.
    board = chess.Board("rnbqkbnr/ppppp1pp/5p2/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    bot = EndgameBot(chess.WHITE)
    move = chess.Move.from_uci("d1h5")  # Qh5+
    enemy_king = board.king(chess.BLACK)

    base_score, _ = bot.evaluate_move(
        board,
        move,
        enemy_king,
        context,
    )
    ahead_score, _ = bot.evaluate_move(
        board,
        move,
        enemy_king,
        GameContext(material_diff=2),
    )

    assert ahead_score > base_score
