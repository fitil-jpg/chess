import chess
import random

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
            Shared game context (unused in this bot).
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
            score, _ = self.evaluate_move(board, move, enemy_king_sq)
            tmp = board.copy(stack=False)
            tmp.push(move)
            score += evaluator.position_score(tmp, self.color)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        move = random.choice(best_moves) if best_moves else None
        return move, float(best_score if best_moves else 0.0)

    def evaluate_move(self, board, move, enemy_king_sq):
        score = 0
        reason = ""
        temp = board.copy()
        temp.push(move)
        if temp.is_check():
            from_sq = move.to_square
            defenders = temp.attackers(self.color, from_sq)
            if defenders:
                score += 100
                reason = "check, protected"
            else:
                score += 50
                reason = "check"
        piece = board.piece_at(move.from_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            before = chess.square_distance(move.from_square, enemy_king_sq)
            after = chess.square_distance(move.to_square, enemy_king_sq)
            if after < before:
                score += 20
                if not reason:
                    reason = "closer to king"
        score += random.uniform(0, 0.2)
        return score, reason
