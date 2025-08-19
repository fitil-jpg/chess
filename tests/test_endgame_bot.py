import random
import chess

from chess_ai.endgame_bot import EndgameBot
from utils import GameContext


def test_check_bonus_scaled_by_material():
    board = chess.Board()
    bot = EndgameBot(chess.WHITE)
    move = chess.Move.from_uci("d1h5")  # Qh5+
    enemy_king = board.king(chess.BLACK)

    random.seed(0)
    base_score, _ = bot.evaluate_move(
        board,
        move,
        enemy_king,
        GameContext(),
    )
    random.seed(0)
    ahead_score, _ = bot.evaluate_move(
        board,
        move,
        enemy_king,
        GameContext(material_diff=2),
    )

    assert ahead_score > base_score
