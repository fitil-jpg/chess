import chess
import random

class EndgameBot:
    def __init__(self, color):
        self.color = color

    def choose_move(self, board, debug=False):
        best_score = float('-inf')
        best_moves = []
        best_reason = ""
        enemy_king_sq = board.king(not self.color)
        for move in board.legal_moves:
            score, reason = self.evaluate_move(board, move, enemy_king_sq)
            if score > best_score:
                best_score = score
                best_moves = [(move, reason)]
            elif score == best_score:
                best_moves.append((move, reason))
        if best_moves:
            move, reason = random.choice(best_moves)
            return (move, reason) if debug else move
        return (None, "no moves") if debug else None

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
