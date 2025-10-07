from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

import chess

from core.evaluator import Evaluator
try:
    # Optional: reuse existing depth-2 forcing threat logic
    from .bot_agent import ThreatScout  # type: ignore
except Exception:  # pragma: no cover - available in most environments
    ThreatScout = None  # type: ignore


class CriticalBot:
    """Agent that targets high-threat opponent pieces.

    The bot uses :class:`Evaluator.criticality` to identify the most critical
    opponent pieces and prefers moves that capture them.  If no such capture is
    available the bot yields ``(None, 0.0)`` allowing other agents to decide.
    """

    def __init__(self, color: bool, capture_bonus: float = 100.0) -> None:
        self.color = color
        self.capture_bonus = capture_bonus

    def choose_move(
        self,
        board: chess.Board,
        context=None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        evaluator = evaluator or Evaluator(board)

        # 1) Immediate mate-in-1
        for mv in board.legal_moves:
            piece = board.piece_at(mv.from_square)
            if not piece or piece.color != self.color:
                continue
            tmp = board.copy(stack=False); tmp.push(mv)
            if tmp.is_checkmate():
                if debug:
                    logger.debug("CriticalBot: mate-in-1 via %s", board.san(mv))
                return mv, 10000.0

        # 2) Depth-2 forcing threats (checks, forks, hanging captures), maximin
        if ThreatScout is not None and board.turn == self.color:
            try:
                scout = ThreatScout(self.color)
                m1, info = scout.probe_depth2(board)
                if m1 is not None:
                    score = float(info.get("min_score_after_reply", 0)) + 500.0
                    if debug:
                        logger.debug(
                            "CriticalBot: forcing threat %s | info=%s | score=%.1f",
                            board.san(m1), info, score,
                        )
                    return m1, score
            except Exception as ex:  # pragma: no cover - defensive
                if debug:
                    logger.debug("CriticalBot: ThreatScout failed: %s", ex)

        # 3) Fallback: target critical enemy pieces, plus forks/hanging
        critical = evaluator.criticality(board, self.color)
        critical_squares = {sq for sq, _ in (critical or [])}

        best_move = None
        best_score = float("-inf")
        enemy = not self.color

        for move in board.legal_moves:
            piece = board.piece_at(move.from_square)
            if not piece or piece.color != self.color:
                continue

            # Avoid obviously losing destinations
            tmp = board.copy(stack=False); tmp.push(move)
            to_sq = move.to_square
            attackers = len(tmp.attackers(enemy, to_sq))
            defenders = len(tmp.attackers(self.color, to_sq))
            if attackers > defenders:
                continue

            score = 0.0

            # Prefer capturing a critical piece
            if move.to_square in critical_squares and board.piece_at(move.to_square):
                score += self.capture_bonus

            # Capture undefended (hanging) targets
            if board.is_capture(move):
                before_piece = board.piece_at(move.to_square)
                if before_piece and before_piece.color == enemy:
                    defn = len(board.attackers(enemy, move.to_square))
                    if defn == 0:
                        score += self.capture_bonus * 0.8 + 50.0
                    else:
                        score += 20.0

            # Check bonus
            if tmp.is_check():
                score += 35.0

            # Knight fork heuristic: landing knight attacks >=2 valuable targets
            if piece.piece_type == chess.KNIGHT:
                valuable = {chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT}
                val_targets = 0
                for t in tmp.attacks(to_sq):
                    q = tmp.piece_at(t)
                    if q and q.color == enemy and q.piece_type in valuable:
                        val_targets += 1
                if val_targets >= 2:
                    score += 70.0

            if score > best_score:
                best_score = score
                best_move = move

        if best_move is not None and best_score > 0.0:
            if debug:
                logger.debug(
                    "CriticalBot: fallback selects %s with score %.1f",
                    board.san(best_move), best_score,
                )
            return best_move, best_score

        return None, 0.0