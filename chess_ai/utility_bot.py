import logging
logger = logging.getLogger(__name__)

import chess

from core.evaluator import Evaluator

class UtilityBot:
    def __init__(self, color: bool):
        self.color = color

    def choose_move(self, board, evaluator: Evaluator | None = None, debug: bool = True):
        """Select a move based on simple utility heuristics.

        Returns a tuple of ``(move, confidence)`` where confidence is the
        heuristic score.  This bot is primarily used for feature extraction and
        testing, hence a single best move is sufficient.
        """

        evaluator = evaluator or Evaluator(board)

        moves = list(board.legal_moves)
        best_moves = []
        top_score = float("-inf")

        for move in moves:
            score = evaluator.score_move(move, self.color)
            if score > top_score:
                best_moves = [move]
                top_score = score
            elif score == top_score:
                best_moves.append(move)

        if not best_moves:
            return None, 0.0
        chosen_move = best_moves[0]
        return chosen_move, float(top_score)

def piece_value(piece):
    values = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, chess.ROOK:5, chess.QUEEN:9, chess.KING:0}
    return values.get(piece.piece_type, 0)