"""
evaluator.py — будує feature map для ходу:
- чи це взяття
- чи ціль не захищена (підвішена)
- інші фактори для майбутнього (центр, шах, захист тощо)
"""

import chess

from core.evaluator import Evaluator as CoreEvaluator

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
        # --- додаткові ознаки активності та відкритих ліній ---

        # Порахувати активність фігури: кількість доступних ходів після виконання
        # цього ходу. Для цього тимчасово застосовуємо хід.
        self.board.push(move)
        piece_sq = move.to_square
        piece_color = not self.board.turn  # колір, що зробив хід
        piece = self.board.piece_at(piece_sq)

        # Кількість можливих ходів (ігноруємо клітини з власними фігурами)
        attacks = self.board.attacks(piece_sq)
        mobility = sum(1 for sq in attacks if self.board.color_at(sq) != piece_color)
        features["active_piece"] = mobility

        # Перевіряємо, чи вийшла фігура на повністю відкриту вертикаль
        if piece and piece.piece_type in (chess.ROOK, chess.QUEEN):
            file_idx = chess.square_file(piece_sq)
            open_file = True
            for rank in range(8):
                sq = chess.square(file_idx, rank)
                if sq != piece_sq and self.board.piece_at(sq):
                    open_file = False
                    break
            features["on_open_file"] = open_file
        else:
            features["on_open_file"] = False

        # Відкрита лінія на короля суперника
        enemy_king = self.board.king(self.board.turn)
        open_to_king = False
        if piece:
            if piece_sq in self.board.attackers(piece_color, enemy_king):
                open_to_king = True
            else:
                ray = self.board.ray(piece_sq, enemy_king)
                if ray and all(not self.board.piece_at(sq) for sq in ray):
                    open_to_king = True
        features["open_file_to_king"] = open_to_king

        # Скасовуємо тимчасовий хід
        self.board.pop()

        # Можеш легко додати більше ознак (контроль центру, шах і тп)
        return features

    def criticality(self, board=None, color: bool | None = None):
        """Proxy to :class:`core.evaluator.Evaluator.criticality`."""

        board = board or self.board
        core = CoreEvaluator(board)
        return core.criticality(board, color)
