import chess

from .chess_bot import ChessBot, calculate_king_value
from utils import GameContext
from core.evaluator import Evaluator


class KingValueBot(ChessBot):
    """Variant of :class:`ChessBot` that rewards lowering the opponent's king value.

    The bot uses :func:`calculate_king_value` to compute how a move changes the
    dynamic material value of the enemy king.  Moves that reduce this value –
    typically by trading off the opponent's material – receive an additional
    bonus in the evaluation score.
    """

    def evaluate_move(self, board: chess.Board, move: chess.Move, context: GameContext | None = None):
        score, reason = super().evaluate_move(board, move, context)
        opp_color = not self.color
        before = calculate_king_value(board, opp_color)
        tmp = board.copy(stack=False)
        tmp.push(move)
        after = calculate_king_value(tmp, opp_color)
        delta = before - after
        if delta:
            score += delta
            bonus_reason = f"king value pressure (+{delta})"
            reason = f"{reason} | {bonus_reason}" if reason else bonus_reason
        return score, reason


__all__ = ["KingValueBot"]
