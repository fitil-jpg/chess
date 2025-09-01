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
            src = board.piece_at(move.from_square)
            tgt = board.piece_at(move.to_square)
            score = 0

            # Дати шах
            if board.gives_check(move):
                score = 100
            # Capture
            elif board.is_capture(move) and tgt:
                tgt_val = piece_value(tgt)
                src_val = piece_value(src)
                attackers = board.attackers(not self.color, move.to_square)
                defended = len(attackers) > 0
                hanging = not defended
                if hanging:
                    score = 90 + tgt_val
                elif tgt_val > src_val:
                    score = 80 + tgt_val - src_val
                else:
                    score = 60 + tgt_val - src_val
            # Attack (не capture)
            elif tgt and tgt.color != self.color:
                tgt_val = piece_value(tgt)
                attackers = board.attackers(self.color, move.to_square)
                defended = len(attackers) > 0
                hanging = not defended
                if hanging:
                    score = 70 + tgt_val
                else:
                    score = 50 + tgt_val
            # Просто хід → score = 0

            if score > top_score:
                best_moves = [move]
                top_score = score
            tmp = board.copy(stack=False)
            tmp.push(move)
            score += evaluator.position_score(tmp, self.color)

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