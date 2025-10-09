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

        # 1) Dynamic king material pressure (existing heuristic)
        before_kv = calculate_king_value(board, opp_color)
        tmp = board.copy(stack=False)
        tmp.push(move)
        after_kv = calculate_king_value(tmp, opp_color)
        kv_delta = before_kv - after_kv
        if kv_delta:
            score += kv_delta
            kv_reason = f"king value pressure (+{kv_delta})"
            reason = f"{reason} | {kv_reason}" if reason else kv_reason

        # 2) Rich king-safety deltas using Evaluator.king_safety
        #    Components include open/semi-open files, attacker counts, pawn storms, proximity.
        self_before_ks = Evaluator.king_safety(board, self.color)
        opp_before_ks = Evaluator.king_safety(board, opp_color)
        self_after_ks = Evaluator.king_safety(tmp, self.color)
        opp_after_ks = Evaluator.king_safety(tmp, opp_color)

        # Positive if we worsened opponent safety (more danger) and improved ours.
        opp_delta = opp_before_ks - opp_after_ks
        self_delta = self_after_ks - self_before_ks

        # Modest weights to keep the signal balanced with base evaluation.
        W_OPP = 4
        W_SELF = 3
        ks_bonus = 0
        if opp_delta:
            ks_bonus += W_OPP * opp_delta
        if self_delta:
            ks_bonus += W_SELF * self_delta
        if ks_bonus:
            score += ks_bonus
            ks_reason = (
                f"king safety Δ (opp {opp_delta:+}, self {self_delta:+}) (+{ks_bonus})"
            )
            reason = f"{reason} | {ks_reason}" if reason else ks_reason

        return score, reason


__all__ = ["KingValueBot"]