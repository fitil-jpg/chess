import logging
logger = logging.getLogger(__name__)

class GamePhaseDetector:
    @staticmethod
    def detect(board):
        """Determine game phase based on remaining pieces.

        Supports both custom boards exposing ``get_all_pieces`` and
        python-chess boards via ``piece_map``.
        """
        if hasattr(board, "get_all_pieces"):
            piece_count = len(board.get_all_pieces())
        elif hasattr(board, "piece_map"):
            piece_count = len(board.piece_map())
        else:  # fallback
            piece_count = 0
        if piece_count > 20:
            return "opening"
        if piece_count < 10:
            return "endgame"
        return "middlegame"