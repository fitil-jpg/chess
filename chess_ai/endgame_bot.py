import logging
logger = logging.getLogger(__name__)

import chess

from core.evaluator import Evaluator
from core.phase import GamePhaseDetector
from utils import GameContext


_SHARED_EVALUATOR: Evaluator | None = None

class EndgameBot:
    def __init__(self, color: bool):
        self.color = color

    @staticmethod
    def _phase_piece_values(phase: str) -> dict[int, int]:
        """Return phase-scaled piece values in centipawns."""
        base = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0,
        }
        if phase == "endgame":
            eg = base.copy()
            eg[chess.KNIGHT] = int(base[chess.KNIGHT] * 0.9)
            eg[chess.BISHOP] = int(base[chess.BISHOP] * 1.05)
            return eg
        return base

    @staticmethod
    def _is_passed_pawn(board: chess.Board, sq: int, color: bool) -> bool:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        enemy = not color
        for ep in board.pieces(chess.PAWN, enemy):
            ef = chess.square_file(ep)
            er = chess.square_rank(ep)
            if abs(ef - file) <= 1:
                if color == chess.WHITE and er > rank:
                    return False
                if color == chess.BLACK and er < rank:
                    return False
        return True

    @staticmethod
    def _fastest_promotion_steps(board: chess.Board, color: bool) -> tuple[int | None, int | None]:
        best_steps: int | None = None
        best_pawn: int | None = None
        for sq in board.pieces(chess.PAWN, color):
            if not EndgameBot._is_passed_pawn(board, sq, color):
                continue
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)
            steps = (7 - rank) if color == chess.WHITE else rank
            blocked_penalty = 0
            dr = 1 if color == chess.WHITE else -1
            r = rank + dr
            while 0 <= r < 8:
                ahead_sq = chess.square(file, r)
                if board.piece_at(ahead_sq):
                    blocked_penalty = 2
                    break
                r += dr
            steps += blocked_penalty
            if best_steps is None or steps < best_steps:
                best_steps = steps
                best_pawn = sq
        return best_steps, best_pawn

    @staticmethod
    def _opposition_bonus(board: chess.Board, color: bool) -> int:
        our_k = board.king(color)
        their_k = board.king(not color)
        if our_k is None or their_k is None:
            return 0
        dist = chess.square_distance(our_k, their_k)
        if dist != 2:
            return 0
        if chess.square_file(our_k) == chess.square_file(their_k) or chess.square_rank(our_k) == chess.square_rank(their_k):
            return 15
        return 0

    @staticmethod
    def _king_activity_bonus(before_board: chess.Board, after_board: chess.Board, move: chess.Move, enemy_king_sq: int, phase: str, color: bool) -> int:
        if phase != "endgame":
            return 0
        piece = before_board.piece_at(move.from_square)
        if not piece or piece.piece_type != chess.KING:
            return 0
        centers = [chess.D4, chess.E4, chess.D5, chess.E5]
        def best_center_dist(sq: int) -> int:
            return min(chess.square_distance(sq, c) for c in centers)
        before = best_center_dist(move.from_square)
        after = best_center_dist(move.to_square)
        bonus = 0
        if after < before:
            bonus += (before - after) * 10
        if enemy_king_sq is not None:
            bef = chess.square_distance(move.from_square, enemy_king_sq)
            aft = chess.square_distance(move.to_square, enemy_king_sq)
            if aft < bef:
                bonus += 5
        return bonus

    @staticmethod
    def _rook_behind_passer_bonus(board: chess.Board, color: bool) -> int:
        bonus = 0
        # Our rooks behind our passed pawns
        for rp in board.pieces(chess.ROOK, color):
            rf = chess.square_file(rp)
            rr = chess.square_rank(rp)
            for pp in board.pieces(chess.PAWN, color):
                if not EndgameBot._is_passed_pawn(board, pp, color):
                    continue
                pf = chess.square_file(pp)
                pr = chess.square_rank(pp)
                if rf != pf:
                    continue
                if color == chess.WHITE and rr < pr:
                    bonus += 20
                if color == chess.BLACK and rr > pr:
                    bonus += 20
        # Our rooks behind enemy passed pawns (restrain)
        enemy = not color
        for rp in board.pieces(chess.ROOK, color):
            rf = chess.square_file(rp)
            rr = chess.square_rank(rp)
            for pp in board.pieces(chess.PAWN, enemy):
                if not EndgameBot._is_passed_pawn(board, pp, enemy):
                    continue
                pf = chess.square_file(pp)
                pr = chess.square_rank(pp)
                if rf != pf:
                    continue
                if enemy == chess.WHITE and rr < pr:
                    bonus += 15
                if enemy == chess.BLACK and rr > pr:
                    bonus += 15
        return bonus

    def choose_move(
        self,
        board: chess.Board,
        context: GameContext | None = None,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Choose move based on endgame heuristics.

        Parameters
        ----------
        board: chess.Board
            Position to analyse.
        context: GameContext | None, optional
            Shared game context.  ``material_diff`` and ``king_safety`` are
            used to slightly tweak the heuristics.
        evaluator: Evaluator | None, optional
            Reusable evaluator instance.  A shared one is created if ``None``.
        debug: bool, optional
            Unused compatibility flag.

        Returns
        -------
        tuple[chess.Move | None, float]
            Selected move and its heuristic score.
        """

        global _SHARED_EVALUATOR
        evaluator = evaluator or _SHARED_EVALUATOR
        if evaluator is None:
            evaluator = _SHARED_EVALUATOR = Evaluator(board)

        best_score = float("-inf")
        best_moves = []
        enemy_king_sq = board.king(not self.color)
        phase = GamePhaseDetector.detect(board)
        for move in board.legal_moves:
            score, _ = self.evaluate_move(board, move, enemy_king_sq, context)
            tmp = board.copy(stack=False)
            tmp.push(move)
            pos = evaluator.position_score(tmp, self.color)
            if phase == "endgame":
                pos = int(pos * 1.1)
            score += pos
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        # Choose a deterministic best move to avoid flaky tests.  Ties are
        # broken by the move's UCI string.
        move = min(best_moves, key=lambda m: m.uci()) if best_moves else None
        return move, float(best_score if best_moves else 0.0)

    def evaluate_move(
        self,
        board: chess.Board,
        move: chess.Move,
        enemy_king_sq: int,
        context: GameContext | None = None,
    ):
        score = 0
        reason = ""
        temp = board.copy()
        temp.push(move)
        phase = GamePhaseDetector.detect(board)
        if temp.is_check():
            from_sq = move.to_square
            defenders = temp.attackers(self.color, from_sq)
            bonus = 100 if defenders else 50
            if context:
                # Reward checks more when ahead in material and penalize when
                # behind.  Also nudge the score based on our own king safety
                # (negative safety reduces the bonus).
                bonus += context.material_diff * 10
                bonus += context.king_safety
            score += bonus
            reason = "check, protected" if defenders else "check"
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            before = chess.square_distance(move.from_square, enemy_king_sq)
            after = chess.square_distance(move.to_square, enemy_king_sq)
            if after < before:
                score += 20
                if not reason:
                    reason = "closer to king"
        # Phase-scaled captures
        if board.is_capture(move):
            pv = self._phase_piece_values(phase)
            tgt = board.piece_at(move.to_square)
            frm = board.piece_at(move.from_square)
            if tgt and frm:
                score += pv.get(tgt.piece_type, 0) - pv.get(frm.piece_type, 0)
        # Endgame heuristics
        if phase == "endgame":
            score += self._king_activity_bonus(board, temp, move, enemy_king_sq, phase, self.color)
            score += self._opposition_bonus(temp, self.color)
            ours_steps, _ = self._fastest_promotion_steps(temp, self.color)
            theirs_steps, _ = self._fastest_promotion_steps(temp, not self.color)
            if ours_steps is not None and theirs_steps is not None:
                score += (theirs_steps - ours_steps) * 10
            elif ours_steps is not None:
                score += 10
            elif theirs_steps is not None:
                score -= 10
            score += self._rook_behind_passer_bonus(temp, self.color)
        # Make evaluation deterministic by avoiding random jitter.
        return score, reason