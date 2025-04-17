class GamePhaseDetector:
    @staticmethod
    def detect(board):
        # Визначення фази гри на основі кількості фігур
        piece_count = len(board.get_all_pieces())
        if piece_count > 20:
            return "opening"
        elif piece_count < 10:
            return "endgame"
        return "middlegame"
