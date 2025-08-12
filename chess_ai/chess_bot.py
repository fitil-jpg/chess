import chess
import random

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]

class ChessBot:
    def __init__(self, color):
        self.color = color

    def choose_move(self, board, debug=False):
        best_score = float('-inf')
        best_moves = []
        best_reason = ""
        for move in board.legal_moves:
            score, reason = self.evaluate_move(board, move)
            if score > best_score:
                best_score = score
                best_moves = [(move, reason)]
            elif score == best_score:
                best_moves.append((move, reason))
        move, reason = random.choice(best_moves) if best_moves else (None, "")
        if debug:
            return move, reason
        return move

    def evaluate_move(self, board, move):
        score = 0
        reasons = []
        opp_color = not self.color
        opp_king_sq = board.king(opp_color)

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
        # 5. Захоплення підвішеної фігури
        if board.is_capture(move):
            target_sq = move.to_square
            defenders = board.attackers(not board.turn, target_sq)
            if not defenders:
                score += 100
                reasons.append("capture hanging")
            else:
                score += 20
                reasons.append("capture defended")
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
