import chess

from core.evaluator import Evaluator
from utils import GameContext


_SHARED_EVALUATOR: Evaluator | None = None

class EndgameBot:
    def __init__(self, color: bool):
        self.color = color

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
        for move in board.legal_moves:
            score, _ = self.evaluate_move(board, move, enemy_king_sq, context)
            tmp = board.copy(stack=False)
            tmp.push(move)
            score += evaluator.position_score(tmp, self.color)
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
        # Make evaluation deterministic by avoiding random jitter.
        return score, reason
