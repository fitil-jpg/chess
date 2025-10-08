import logging
logger = logging.getLogger(__name__)

from pathlib import Path
import chess
from core.evaluator import Evaluator, piece_value
from core.pattern_loader import PatternResponder
from .see import static_exchange_eval
from .risk_analyzer import RiskAnalyzer


class TrapBot:
    """Bot that hunts for traps by reducing opponent mobility."""

    def __init__(self, color: bool):
        self.color = color
        self._risk = RiskAnalyzer()
        self._trap_responder: PatternResponder | None = None

    def _load_traps(self) -> None:
        """Lazily load trap patterns from `configs/traps.json` if present."""
        if self._trap_responder is not None:
            return
        cfg = Path("configs/traps.json")
        if cfg.exists():
            try:
                self._trap_responder = PatternResponder.from_file(cfg)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to load trap patterns: %s", exc)
                self._trap_responder = None

    def _opponent_label(self) -> str:
        return "black" if self.color == chess.WHITE else "white"

    def choose_move(
        self,
        board: chess.Board,
        context=None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return the move that most limits opponent mobility.

        The bot evaluates every legal move by simulating it and checking the
        change in mobility of the opponent's pieces using
        :meth:`Evaluator.mobility`.  It also looks one ply ahead by allowing the
        targeted piece to make a reply and taking the best mobility it can
        achieve.  The move causing the largest mobility drop for any single
        opponent piece is selected.
        """

        evaluator = evaluator or Evaluator(board)
        # Optional trap pattern for current board
        self._load_traps()
        pattern_move: chess.Move | None = None
        trap_factor_safe = 1.25  # bonus for safe traps
        trap_factor_risky = 0.50  # downgrade risky traps rather than forbidding
        if self._trap_responder is not None:
            action = self._trap_responder.match(board)
            if action:
                try:
                    candidate = chess.Move.from_uci(action)
                    if candidate in board.legal_moves:
                        pattern_move = candidate
                except Exception:  # pragma: no cover - invalid action ignored
                    pattern_move = None
        evaluator.mobility(board)
        pre_stats = evaluator.mobility_stats[self._opponent_label()]["pieces"]

        best_move: chess.Move | None = None
        best_drop = float("-inf")

        for mv in board.legal_moves:
            tmp = board.copy(stack=False)
            tmp.push(mv)

            after_eval = Evaluator(tmp)
            after_eval.mobility(tmp)
            after_stats = after_eval.mobility_stats[self._opponent_label()]["pieces"]

            # Compare mobility for each opponent piece. ``move_drop`` tracks the
            # largest reduction (which may be negative if all candidate moves
            # increase the opponent's mobility). Starting at ``-inf`` ensures we
            # don't ignore moves that worsen the position.
            move_drop = float("-inf")
            for sq, info in pre_stats.items():
                pre_mob = info["mobility"]
                post_info = after_stats.get(sq)
                was_capture = False
                # Depth preference is relative to the targeted piece's zone,
                # not our move destination, to avoid overvaluing incidental checks.
                rank_sq = chess.square_rank(sq)
                depth = rank_sq + 1 if self.color == chess.WHITE else 8 - rank_sq
                if post_info is None:
                    drop = pre_mob  # piece captured
                    was_capture = True
                else:
                    drop = pre_mob - post_info["mobility"]
                    # Look ahead: piece tries to escape
                    replies = [m for m in tmp.legal_moves if m.from_square == sq]
                    if replies:
                        max_mob = post_info["mobility"]
                        for r in replies:
                            tmp.push(r)
                            reply_eval = Evaluator(tmp)
                            reply_eval.mobility(tmp)
                            reply_stats = reply_eval.mobility_stats[self._opponent_label()]["pieces"]
                            new_sq = r.to_square
                            max_mob = max(
                                max_mob,
                                reply_stats.get(new_sq, {"mobility": 0})["mobility"],
                            )
                            tmp.pop()
                        drop = pre_mob - max_mob

                # Weight the drop by the piece's initial mobility and how deep
                # the trap lies to prioritise high-mobility targets and deeper
                # incursions.
                weighted_drop = drop * pre_mob * depth
                if was_capture:
                    # Slightly prefer capturing highly mobile targets
                    weighted_drop *= 1.15

                # If this move matches a trap pattern, apply SEE + 1-ply safety
                # gating: reward safe traps, downgrade risky ones.
                if pattern_move is not None and mv == pattern_move:
                    see_score = static_exchange_eval(board, mv)
                    risky = self._risk.is_risky(board, mv, depth=1)
                    if see_score >= 0 and not risky:
                        weighted_drop *= trap_factor_safe
                    else:
                        weighted_drop *= trap_factor_risky
                if weighted_drop > move_drop:
                    move_drop = weighted_drop

            if move_drop > best_drop:
                best_drop = move_drop
                best_move = mv

        if best_move is None:
            return None, 0.0
        return best_move, float(best_drop)
