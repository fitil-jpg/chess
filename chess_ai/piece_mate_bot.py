from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Tuple

import chess

from core.evaluator import Evaluator, escape_squares, is_piece_mated
from metrics.attack_map import attack_count_per_square
from .see import static_exchange_eval
from .threat_map import ThreatMap
from utils import GameContext


logger = logging.getLogger(__name__)


class PieceMateBot:
    """Bot that prioritises trapping ("mating") a chosen enemy piece.

    A non-king piece is considered "mated" if its current square is attacked
    and it has no safe legal move (including captures) that lands on a square
    not attacked by our side. This uses :func:`is_piece_mated` semantics.

    Strategy:
    - Focus a target class of enemy pieces (e.g. all knights) or auto-pick
      the thinnest enemy pieces from :class:`ThreatMap`.
    - Score moves by how much they increase the count of mated target pieces
      and reduce those targets' safe escape moves.
    - Use a small positional tiebreak and SEE to avoid outright blunders.
    """

    def __init__(
        self,
        color: bool,
        *,
        target_piece_type: Optional[int] = None,
        max_targets: int = 3,
        safe_only: bool = False,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.color = color
        self.target_piece_type = target_piece_type
        self.max_targets = max(1, int(max_targets))
        self.safe_only = safe_only
        self.W: Dict[str, float] = {
            # Primary objectives
            "mate": 800.0,            # increase in mated target pieces
            "reduce_escape": 15.0,    # reduction of total escape moves across targets
            # Pressure heuristics
            "pressure": 2.5,          # increase in (our_attackers - their_defenders) on targets
            # Tactical prudence / tie-breakers
            "see": 1.0,               # static exchange eval for captures
            "check": 20.0,            # giving check often reduces enemy freedom globally
            "pos": 0.1,               # light positional nudge
        }
        if weights:
            self.W.update(weights)

        self._shared_evaluator: Optional[Evaluator] = None

    # ------------------ Public API ------------------
    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ) -> Tuple[Optional[chess.Move], float]:
        if board.turn != self.color:
            return None, 0.0

        evalr = evaluator or self._shared_evaluator or Evaluator(board)
        if self._shared_evaluator is None:
            self._shared_evaluator = evalr

        enemy = not self.color
        target_squares = self._select_targets(board, enemy)
        if not target_squares:
            # Fall back to general positional choice if nothing to trap
            return self._fallback_choice(board, evalr)

        baseline = self._targets_stats(board, target_squares)

        best_move: Optional[chess.Move] = None
        best_score: float = float("-inf")
        best_info: Dict[str, float] = {}

        for mv in board.legal_moves:
            tmp = board.copy(stack=False)
            tmp.push(mv)

            # Safety gate when requested: skip moves that obviously worsen
            # SEE on their destination or step into heavy fire.
            if self.safe_only and self._is_obviously_unsafe(board, mv):
                continue

            # Re-evaluate targets on the new position (capture may remove some)
            new_targets = [
                sq for sq in target_squares
                if (pc := tmp.piece_at(sq)) is not None and pc.color == enemy
            ]
            stats_after = self._targets_stats(tmp, new_targets)

            mate_delta = stats_after["mated_count"] - baseline["mated_count"]
            escape_delta = baseline["total_escapes"] - stats_after["total_escapes"]
            pressure_delta = stats_after["pressure"] - baseline["pressure"]

            score = (
                self.W["mate"] * mate_delta
                + self.W["reduce_escape"] * max(0, escape_delta)
                + self.W["pressure"] * max(0, pressure_delta)
            )

            if board.is_capture(mv):
                see_gain = static_exchange_eval(board, mv)
                score += self.W["see"] * see_gain
            else:
                see_gain = 0.0

            if tmp.is_check():
                score += self.W["check"]

            # Light positional tiebreak
            score += self.W["pos"] * evalr.position_score(tmp, self.color)

            if score > best_score or (
                score == best_score and mv.uci() < (best_move.uci() if best_move else "zzzz")
            ):
                best_move = mv
                best_score = float(score)
                best_info = {
                    "mateΔ": float(mate_delta),
                    "escΔ": float(escape_delta),
                    "pressΔ": float(pressure_delta),
                    "see": float(see_gain),
                }

        if debug and best_move is not None:
            logger.debug("PieceMateBot: %s", best_info)
            print(f"PieceMateBot: {best_info}")

        return best_move, float(best_score if best_move is not None else 0.0)

    # ------------------ Internals ------------------
    def _fallback_choice(self, board: chess.Board, evaluator: Evaluator) -> Tuple[Optional[chess.Move], float]:
        best: Optional[chess.Move] = None
        best_score = float("-inf")
        for mv in board.legal_moves:
            tmp = board.copy(stack=False)
            tmp.push(mv)
            s = evaluator.position_score(tmp, self.color)
            if tmp.is_check():
                s += 25.0
            if board.is_capture(mv):
                s += 0.5 * static_exchange_eval(board, mv)
            if s > best_score or (s == best_score and (best is None or mv.uci() < best.uci())):
                best, best_score = mv, float(s)
        return best, float(best_score if best is not None else 0.0)

    def _select_targets(self, board: chess.Board, enemy: bool) -> List[int]:
        # If explicit type requested, gather all enemy squares of that type
        if self.target_piece_type is not None:
            return [
                sq for sq, pc in board.piece_map().items()
                if pc.color == enemy and pc.piece_type == self.target_piece_type
            ]

        # Otherwise pick up to N thinnest enemy pieces (def - att <= 0 first)
        try:
            thin = ThreatMap(enemy).summary(board)["thin_pieces"]
            squares = [sq for (sq, _d, _a) in thin[: self.max_targets]]
            if squares:
                return squares
        except Exception:
            pass

        # Fallback: any enemy pieces, prefer non-pawns and not the king
        candidates: List[Tuple[int, int]] = []
        for sq, pc in board.piece_map().items():
            if pc.color != enemy or pc.piece_type == chess.KING:
                continue
            # Prefer more valuable targets
            val = {
                chess.QUEEN: 9,
                chess.ROOK: 5,
                chess.BISHOP: 3,
                chess.KNIGHT: 3,
                chess.PAWN: 1,
            }.get(pc.piece_type, 0)
            candidates.append((val, sq))
        candidates.sort(reverse=True)
        return [sq for _v, sq in candidates[: self.max_targets]]

    def _is_obviously_unsafe(self, board: chess.Board, move: chess.Move) -> bool:
        if not board.is_capture(move):
            # moving onto a square heavily attacked without defenders is risky
            tmp = board.copy(stack=False)
            tmp.push(move)
            attackers = len(tmp.attackers(not self.color, move.to_square))
            defenders = len(tmp.attackers(self.color, move.to_square))
            return attackers > defenders + 1
        # For captures, rely on SEE
        return static_exchange_eval(board, move) < 0

    def _targets_stats(self, board: chess.Board, target_squares: Sequence[int]) -> Dict[str, float]:
        # Count how many targets are already mated and sum their safe escapes
        mated_count = 0
        total_escapes = 0
        enemy = not self.color
        for sq in target_squares:
            pc = board.piece_at(sq)
            if pc is None or pc.color != enemy:
                continue
            if is_piece_mated(board, sq):
                mated_count += 1
            else:
                total_escapes += len(escape_squares(board, sq))

        # Aggregate pressure (our attackers - their defenders) on targets
        counts = attack_count_per_square(board)
        pressure = 0
        for sq in target_squares:
            pc = board.piece_at(sq)
            if pc is None or pc.color != enemy:
                continue
            our = counts[self.color][sq]
            theirs = counts[enemy][sq]
            pressure += max(0, our - theirs)

        return {
            "mated_count": float(mated_count),
            "total_escapes": float(total_escapes),
            "pressure": float(pressure),
        }


__all__ = ["PieceMateBot"]
