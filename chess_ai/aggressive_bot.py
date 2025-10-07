"""AggressiveBot
==================

Very simple aggressive agent that prefers moves with the largest material
gain.  The bot returns a tuple ``(move, confidence)`` where ``confidence`` is
the estimated material advantage after the move.  Non‑capturing moves have
zero confidence.
"""

from __future__ import annotations

import chess

import logging
logger = logging.getLogger(__name__)

from core.evaluator import Evaluator
from utils import GameContext
from .utility_bot import piece_value
from .see import static_exchange_eval


_SHARED_EVALUATOR: Evaluator | None = None


class AggressiveBot:
    def __init__(self, color: bool, capture_gain_factor: float = 1.5):
        self.color = color
        # Scaling applied to capture gains when we're behind in material.
        self.capture_gain_factor = capture_gain_factor

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return the move that maximises material gain.

        Parameters
        ----------
        board: chess.Board
            Current board state.
        context: GameContext | None, optional
            Shared game context (currently unused).
        evaluator: Evaluator | None, optional
            Reusable evaluator.  If ``None``, a shared instance is created.
        debug: bool, optional
            Unused flag for API compatibility.

        Returns
        -------
        tuple[chess.Move | None, float]
            Selected move and the estimated material gain.
        """

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        moves = list(board.legal_moves)
        if not moves:
            return None, 0.0

        # We select the move using an aggressive priority score (checks/captures/motifs),
        # but we preserve the reported confidence as the historical material-gain score
        # to keep API and tests stable.
        candidates: list[tuple[float, float, chess.Move]] = []  # (priority_score, reported_score, move)

        for move in moves:
            # Reported (backward-compatible) gain component
            gain = 0.0
            is_capture = board.is_capture(move)
            if is_capture:
                captured = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if captured and attacker:
                    gain = piece_value(captured) - piece_value(attacker)
                    # Encourage trades when behind by boosting capture gains.
                    if context and context.material_diff < 0:
                        gain *= self.capture_gain_factor
                        if debug:
                            msg = (
                                f"AggressiveBot: material deficit, scaled capture gain to {gain:.1f}"
                            )
                            logger.debug(msg)
                            print(msg)

            # Compute evaluation after the move once
            tmp = board.copy(stack=False)
            tmp.push(move)
            pos_score = evaluator.position_score(tmp, self.color)

            # Backward-compatible reported score used as confidence
            reported_score = gain + pos_score

            # Aggressive priority scoring: prioritize checks and SEE-safe captures,
            # include light tactical motifs without affecting reported confidence.
            priority = pos_score

            gives_check = board.gives_check(move)
            if gives_check:
                # Strongly prefer checking moves
                priority += 1000.0

            # SEE for captures
            if is_capture:
                see_gain = static_exchange_eval(board, move)
                if see_gain < 0:
                    # Deprioritize tactically bad captures
                    priority -= 500.0
                else:
                    # Reward tactically sound captures
                    priority += 500.0 + 10.0 * see_gain

                # Hanging target motif (undefended before capture)
                defenders = board.attackers(not board.turn, move.to_square)
                if not defenders:
                    priority += 200.0

            # Simple fork motif: after the move, count attacked enemy pieces (>= minor value)
            moved_piece = tmp.piece_at(move.to_square)
            if moved_piece:
                attacked_enemy_squares = [sq for sq in tmp.attacks(move.to_square) if (p := tmp.piece_at(sq)) and p.color != self.color]
                # Count valuable targets (knights or higher)
                valuable_targets = 0
                seen_targets = set()
                for sq in attacked_enemy_squares:
                    if sq in seen_targets:
                        continue
                    seen_targets.add(sq)
                    p = tmp.piece_at(sq)
                    if p and piece_value(p) >= 3:
                        valuable_targets += 1
                if valuable_targets >= 2:
                    priority += 80.0 * valuable_targets

            # Immediate checkmate gets the highest priority
            if tmp.is_checkmate():
                priority += 10000.0

            candidates.append((float(priority), float(reported_score), move))

        if not candidates:
            return None, 0.0

        # Choose by priority, then by reported score, then deterministically by UCI
        candidates.sort(key=lambda t: (t[0], t[1], t[2].uci()))
        best_priority, best_reported, best_move = candidates[-1]
        return best_move, float(best_reported)
