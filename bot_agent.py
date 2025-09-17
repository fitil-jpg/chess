# bot_agent.py
import chess
from evaluation import evaluate

class DynamicBot:
    """
    Дуже простий динамічний бот: depth=1 (оцінює позицію після власного ходу).
    Мета — показати розкладку оцінки + увімкнути PST (не нулі).
    """

    def __init__(self, name: str = "DynamicBot"):
        self.name = name

    def select_move(self, board: chess.Board) -> tuple[chess.Move, dict]:
        best_move = None
        best_score = -10**9
        best_details = {}

        for move in board.legal_moves:
            mover = board.turn
            board.push(move)
            sc, det = evaluate(board)
            board.pop()

            # Якщо хід робить ЧОРНИЙ — загальна оцінка з точки зору БІЛИХ все ще sc,
            # але бот (за чорних) максимізує свою користь, тобто *мінімізує* sc.
            side_factor = 1 if mover == chess.WHITE else -1
            sided_score = side_factor * sc

            if sided_score > best_score:
                best_score = sided_score
                best_move = move
                best_details = det | {"raw_score": sc}

        return best_move, best_details
