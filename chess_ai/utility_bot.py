import chess

class UtilityBot:
    def __init__(self, color):
        self.color = color

    def choose_move(self, board,debug=True):
        moves = list(board.legal_moves)
        best_moves = []
        best_reason = []
        top_score = -9999

        for move in moves:
            src = board.piece_at(move.from_square)
            tgt = board.piece_at(move.to_square)
            reason = None
            score = 0

            # Дати шах
            if board.is_check(move):
                reason = {"type": "check"}
                score = 100
            # Capture
            elif board.is_capture(move) and tgt:
                tgt_val = piece_value(tgt)
                src_val = piece_value(src)
                attackers = board.attackers(not self.color, move.to_square)
                defended = len(attackers) > 0
                hanging = not defended
                reason = {
                    "type": "capture",
                    "target": tgt.symbol().upper(),
                    "value": tgt_val,
                }
                if hanging:
                    reason["hanging"] = True
                    score = 90 + tgt_val
                elif tgt_val > src_val:
                    reason["valuable_capture"] = True
                    score = 80 + tgt_val - src_val
                else:
                    score = 60 + tgt_val - src_val
            # Attack (не capture)
            elif tgt and tgt.color != self.color:
                tgt_val = piece_value(tgt)
                attackers = board.attackers(self.color, move.to_square)
                defended = len(attackers) > 0
                hanging = not defended
                reason = {
                    "type": "attack",
                    "target": tgt.symbol().upper(),
                    "value": tgt_val,
                }
                if hanging:
                    reason["hanging"] = True
                    score = 70 + tgt_val
                else:
                    score = 50 + tgt_val
            # Просто хід
            else:
                reason = {"type": "random"}
                score = 0

            if score > top_score:
                best_moves = [(move, reason)]
                top_score = score
            elif score == top_score:
                best_moves.append((move, reason))

        if not best_moves:
            return None, {"type": "no_move"}
        chosen_move, chosen_reason = best_moves[0]
        return chosen_move, chosen_reason

def piece_value(piece):
    values = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3, chess.ROOK:5, chess.QUEEN:9, chess.KING:0}
    return values.get(piece.piece_type, 0)
