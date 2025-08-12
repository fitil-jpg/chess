"""
decision_engine.py — вибирає найкращий хід на основі пошуку з селективними розширеннями.
"""

import random
import chess


class DecisionEngine:
    def __init__(self):
        # Зберігаємо порожній ініціалізатор для сумісності
        pass

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

    def search(self, board: chess.Board, depth: int) -> int:
        """Negamax-пошук з розширеннями по шаху та взяттю."""
        if depth == 0 or board.is_game_over() or board.is_repetition(3):
            return self._evaluate(board)

        best = float("-inf")
        for move in board.legal_moves:
            extension = 1 if board.is_capture(move) or board.gives_check(move) else 0
            board.push(move)
            score = -self.search(board, depth - 1 + extension)
            board.pop()
            if score > best:
                best = score
        return best if best != float("-inf") else self._evaluate(board)

    def choose_best_move(self, board: chess.Board):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        best_score = float("-inf")
        best_moves = []
        for move in legal_moves:
            extension = 1 if board.is_capture(move) or board.gives_check(move) else 0
            board.push(move)
            score = -self.search(board, extension)
            board.pop()
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        return random.choice(best_moves) if best_moves else random.choice(legal_moves)
