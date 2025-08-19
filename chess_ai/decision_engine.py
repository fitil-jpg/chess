"""
decision_engine.py — вибирає найкращий хід на основі пошуку з селективними розширеннями.
"""

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

        best_move: chess.Move | None = None
        best_score = float("-inf")
        best_capture = -1
        for move in moves_to_consider:
            extension = 1 if board.is_capture(move) or board.gives_check(move) else 0
            target = board.piece_at(move.to_square)
            capture_val = 0 if not target else {
                chess.PAWN: 100,
                chess.KNIGHT: 300,
                chess.BISHOP: 300,
                chess.ROOK: 500,
                chess.QUEEN: 900,
            }.get(target.piece_type, 0)
            board.push(move)
            score = -self.search(board, extension) + capture_val
            board.pop()
            if (
                score > best_score
                or (
                    score == best_score
                    and (capture_val > best_capture or (capture_val == best_capture and (best_move is None or move.to_square > best_move.to_square)))
                )
            ):
                best_score = score
                best_capture = capture_val
                best_move = move

        return best_move if best_move else None
