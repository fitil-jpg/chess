"""
decision_engine.py — вибирає найкращий хід на основі пошуку з селективними розширеннями.
"""

import chess

from core.quiescence import quiescence
from .risk_analyzer import RiskAnalyzer


class DecisionEngine:
    def __init__(self, base_depth: int = 2, material_weight: int = 2):
        """Create a new decision engine.

        Parameters
        ----------
        base_depth:
            Minimum search depth for root moves before selective
            extensions are applied.
        material_weight:
            Multiplier used to emphasise material advantage in the
            evaluation.  Capturing valuable pieces should therefore
            outweigh sequences of repeated checks.
        """

        self.risk_analyzer = RiskAnalyzer()
        self.base_depth = base_depth
        self.material_weight = material_weight

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
        return score * self.material_weight

    def search(self, board: chess.Board, depth: int,
               alpha: int = -float("inf"), beta: int = float("inf")) -> int:
        """Alpha-beta negamax search with simple selective extensions.

        Once the nominal depth is exhausted or the position is terminal,
        the function transitions into a quiescence search to avoid the
        horizon effect.
        """
        if depth == 0 or board.is_game_over() or board.is_repetition(3):
            # Scale the quiescence search to emphasise material balance
            # without distorting the alpha--beta window.
            scaled_alpha = alpha / self.material_weight
            scaled_beta = beta / self.material_weight
            return quiescence(board, scaled_alpha, scaled_beta) * self.material_weight

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

        scored_moves: list[tuple[int, int, chess.Move]] = []
        for move in moves_to_consider:
            extension = 1 if board.is_capture(move) or board.gives_check(move) else 0
            capture_val = 0
            if board.is_capture(move):
                target = board.piece_at(move.to_square)
                capture_val = {
                    chess.PAWN: 100,
                    chess.KNIGHT: 300,
                    chess.BISHOP: 300,
                    chess.ROOK: 500,
                    chess.QUEEN: 900,
                }.get(target.piece_type, 0) if target else 0
            board.push(move)
            score = -self.search(board, self.base_depth + extension)
            board.pop()
            score += capture_val * self.material_weight
            scored_moves.append((score, capture_val, move))

        if not scored_moves:
            return None
        best_score = max(score for score, _, _ in scored_moves)
        best_moves = [m for s, c, m in scored_moves if s == best_score]
        capture_moves = [m for s, c, m in scored_moves if s == best_score and c > 0]
        return capture_moves[0] if capture_moves else best_moves[0]
