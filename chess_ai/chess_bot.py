import chess
import random

from core.utils import GameContext
from core.evaluator import Evaluator
from .risk_analyzer import RiskAnalyzer

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

class ChessBot:
    def __init__(self, color: bool):
        self.color = color
        self.risk_analyzer = RiskAnalyzer()

    def choose_move(
        self,
        board: chess.Board,
        ctx: GameContext,
        evaluator: Evaluator | None = None,
        debug: bool = False,
    ):
        """Return the move with the highest evaluation score.

        The score itself serves as the confidence value.
        """

        evaluator = evaluator or Evaluator(board)

        best_score = float("-inf")
        best_moves = []
        for move in board.legal_moves:
            score, _ = self.evaluate_move(board, move)
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

    def evaluate_move(self, board, move):
        if self.risk_analyzer.is_risky(board, move):
            return float('-inf'), "risky move"

        score = 0
        reasons = []
        opp_color = not self.color
        opp_king_sq = board.king(opp_color)
        repetition = board.is_repetition(2)

        # 1. Кількість safe square у суперника ДО ходу
        before_safe = []
        for m in board.legal_moves:
            if m.from_square == opp_king_sq:
                to_sq = m.to_square
                if not board.is_attacked_by(self.color, to_sq):
                    before_safe.append(to_sq)

        # 2. Кількість safe square у суперника ПІСЛЯ ходу
        temp = board.copy()
        temp.push(move)
        after_safe = []
        opp_king_sq_after = temp.king(opp_color)
        for m in temp.legal_moves:
            if m.from_square == opp_king_sq_after:
                to_sq = m.to_square
                if not temp.is_attacked_by(self.color, to_sq):
                    after_safe.append(to_sq)

        # 3. Якщо safe square стало менше — бонус
        if len(after_safe) < len(before_safe):
            bonus = 100 + (len(before_safe) - len(after_safe)) * 20
            score += bonus
            reasons.append(f"reduced enemy king safe squares: {len(before_safe)}→{len(after_safe)} (+{bonus})")

        # 4. Якщо цей хід атакує нову safe square і під захистом
        if opp_king_sq is not None and move.to_square in before_safe:
            defenders = temp.attackers(self.color, move.to_square)
            attackers = temp.attackers(opp_color, move.to_square)
            if defenders and not attackers:
                score += 40
                reasons.append("attacks king's safe square under protection (+40)")

        # --- стандартна логіка:
        # 5. Захоплення фігури
        if board.is_capture(move):
            target_piece = board.piece_at(move.to_square)
            from_piece = board.piece_at(move.from_square)
            if target_piece and from_piece:
                gain = PIECE_VALUES[target_piece.piece_type] - PIECE_VALUES[from_piece.piece_type]
                score += gain
                defenders = board.attackers(not board.turn, move.to_square)
                if not defenders:
                    score += 100
                    reasons.append(
                        f"capture hanging {target_piece.symbol().upper()} (+{100 + gain})"
                    )
                else:
                    reasons.append(
                        f"capture defended {target_piece.symbol().upper()} (+{gain})"
                    )
                if repetition and gain > 0:
                    score += 150
                    reasons.append(
                        "avoid repetition: capture bonus (+150)"
                    )
        # 6. Центр
        if move.to_square in CENTER_SQUARES:
            score += 30
            reasons.append("center control")
        # 7. Розвиток
        from_sq = move.from_square
        piece = board.piece_at(from_sq)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP] and (from_sq in [chess.B1, chess.G1, chess.B8, chess.G8]):
            score += 10
            reasons.append("develop piece")
        # 8. Promotion
        if move.promotion:
            score += 90
            reasons.append("promotion")
        score += random.uniform(0, 0.2)
        return score, " | ".join(reasons)
