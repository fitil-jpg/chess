import logging
logger = logging.getLogger(__name__)

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

        # Dynamic king value pressure (material-based)
        before_val = calculate_king_value(board, opp_color)
        tmp = board.copy(stack=False)
        tmp.push(move)
        after_val = calculate_king_value(tmp, opp_color)
        delta_val = before_val - after_val

        # Rich king-safety pressure using Evaluator.king_safety
        ks_before = Evaluator.king_safety(board, opp_color)
        ks_after = Evaluator.king_safety(tmp, opp_color)
        # If the opponent's safety gets worse (more negative), we gain bonus.
        # Convert safety change into a small bonus to avoid overpowering.
        ks_improvement = ks_before - ks_after

        total_bonus = 0
        if delta_val:
            total_bonus += delta_val
        if ks_improvement:
            total_bonus += int(ks_improvement)

        if total_bonus:
            score += total_bonus
            bonus_reason = f"king pressure (+{total_bonus})"
            reason = f"{reason} | {bonus_reason}" if reason else bonus_reason
        return score, reason


__all__ = ["KingValueBot"]