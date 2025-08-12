"""
decision_engine.py — вибирає найкращий хід на основі оцінки scorer'а і features від evaluator'а.
"""

from .evaluator import Evaluator
from .scorer import Scorer
import random

class DecisionEngine:
    def __init__(self):
        self.scorer = Scorer()

    def choose_best_move(self, board):
        evaluator = Evaluator(board)
        best_score = float('-inf')
        best_moves = []
        legal_moves = list(board.legal_moves)
        for move in legal_moves:
            features = evaluator.extract_features(move)
            score = self.scorer.score(features)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        # Вибираємо випадково серед найкращих (щоб не грати одне й те саме)
        if best_moves:
            return random.choice(best_moves)
        return random.choice(legal_moves)
