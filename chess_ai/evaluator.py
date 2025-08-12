"""
evaluator.py — будує feature map для ходу:
- чи це взяття
- чи ціль не захищена (підвішена)
- інші фактори для майбутнього (центр, шах, захист тощо)
"""

import chess

class Evaluator:
    def __init__(self, board):
        self.board = board

    def extract_features(self, move):
        """
        Повертає словник feature-ів для цього ходу.
        """
        features = {}
        features["is_capture"] = self.board.is_capture(move)

        # Підвішена: це взяття і ціль не захищена
        if features["is_capture"]:
            target_sq = move.to_square
            defenders = self.board.attackers(not self.board.turn, target_sq)
            features["target_is_hanging"] = not bool(defenders)
        else:
            features["target_is_hanging"] = False

        # Можеш легко додати більше ознак (контроль центру, шах і тп)
        return features
