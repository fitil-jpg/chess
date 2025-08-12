import random
from .chess_bot import ChessBot
from .endgame_bot import EndgameBot
from .random_bot import RandomBot
from .utility_bot import piece_value

class DynamicBot:
    def __init__(self, color):
        self.center = ChessBot(color)
        self.endgame = EndgameBot(color)
        self.random = RandomBot(color)
        self.color = color

    def choose_move(self, board, debug=True):
        # -1. Якщо позиція повторюється >=2 разів, шукаємо позитивний захват
        if board.is_repetition(2):
            rep_caps = []
            for move in board.legal_moves:
                if board.is_capture(move):
                    score, _ = self.center.evaluate_move(board, move)
                    if score > 0:
                        rep_caps.append((move, score))
            if rep_caps:
                move, score = max(rep_caps, key=lambda x: x[1])
                if debug:
                    return move, "DynamicBot: REPETITION CAPTURE"
                return move
        # 0. Якщо можна вигідно забрати фігуру — робимо це
        capture_moves = []
        for move in board.legal_moves:
            if board.is_capture(move):
                src = board.piece_at(move.from_square)
                tgt = board.piece_at(move.to_square)
                if src and tgt:
                    defenders = board.attackers(not self.color, move.to_square)
                    if not defenders or piece_value(tgt) > piece_value(src):
                        capture_moves.append((move, piece_value(tgt)))
        if capture_moves:
            move = max(capture_moves, key=lambda x: x[1])[0]
            if debug:
                return move, "DynamicBot: CAPTURE"
            return move

        # 1. Якщо можна safe-check (шах з під захистом) — EndgameBot
        for move in board.legal_moves:
            temp = board.copy()
            temp.push(move)
            if temp.is_check():
                defenders = temp.attackers(self.color, move.to_square)
                if defenders:
                    if debug:
                        move_, reason = self.endgame.choose_move(board, debug=True)
                        return move_, f"DynamicBot: SAFE CHECK: {reason}"
                    return self.endgame.choose_move(board)
        # 2. Якщо ≤ 7 своїх фігур — ендшпіль
        if sum(1 for p in board.piece_map().values() if p.color == self.color) <= 7:
            if debug:
                move_, reason = self.endgame.choose_move(board, debug=True)
                return move_, f"DynamicBot: ENDGAME: {reason}"
            return self.endgame.choose_move(board)
        # 3. Якщо мобільність менше 8 — RandomBot (шукати нестандартний хід)
        mobility = len([m for m in board.legal_moves])
        if mobility < 8:
            if debug:
                move_, reason = self.random.choose_move(board, debug=True)
                return move_, f"DynamicBot: LOW MOBILITY: {reason}"
            return self.random.choose_move(board)
        # 4. Інакше CenterBot
        if debug:
            move_, reason = self.center.choose_move(board, debug=True)
            return move_, f"DynamicBot: CENTER: {reason}"
        return self.center.choose_move(board)
