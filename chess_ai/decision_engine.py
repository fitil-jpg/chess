"""
decision_engine.py — вибирає найкращий хід на основі пошуку з селективними розширеннями.
"""

import random
import chess

from core.quiescence import quiescence
from .risk_analyzer import RiskAnalyzer


class DecisionEngine:
    def __init__(self):
        # Зберігаємо порожній ініціалізатор для сумісності
        self.risk_analyzer = RiskAnalyzer()

    def _evaluate(self, board: chess.Board) -> int:
        """Проста матеріальна оцінка позиції з точки зору гравця, який ходить."""
        values = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 300,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0,
        }
        score = 0
        for piece, val in values.items():
            score += len(board.pieces(piece, board.turn)) * val
            score -= len(board.pieces(piece, not board.turn)) * val
        return score

    def search(self, board: chess.Board, depth: int,
               alpha: int = -float("inf"), beta: int = float("inf")) -> int:
        """Alpha-beta negamax search with simple selective extensions.

        Once the nominal depth is exhausted or the position is terminal,
        the function transitions into a quiescence search to avoid the
        horizon effect.
        """
        if depth == 0 or board.is_game_over() or board.is_repetition(3):
            return quiescence(board, alpha, beta)

        best = float("-inf")
        for move in board.legal_moves:
            extension = 1 if board.is_capture(move) or board.gives_check(move) else 0
            board.push(move)
            score = -self.search(board, depth - 1 + extension, -beta, -alpha)
            board.pop()

            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        if best == float("-inf"):
            return quiescence(board, alpha, beta)
        return best

    def choose_best_move(self, board: chess.Board):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        safe_moves = [m for m in legal_moves if not self.risk_analyzer.is_risky(board, m)]
        moves_to_consider = safe_moves if safe_moves else legal_moves

        best_score = float("-inf")
        best_moves = []
        for move in moves_to_consider:
            is_capture = board.is_capture(move)
            extension = 1 if is_capture or board.gives_check(move) else 0
            capture_value = 0
            if is_capture:
                target = board.piece_at(move.to_square)
                if target:
                    capture_value = self.risk_analyzer.values.get(target.piece_type, 0)
            board.push(move)
            score = -self.search(board, extension) + capture_value
            board.pop()
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        if not best_moves:
            return random.choice(moves_to_consider)

        capturing = [m for m in best_moves if board.is_capture(m)]
        pool = capturing if capturing else best_moves
        return random.choice(pool)
