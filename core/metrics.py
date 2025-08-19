# metrics.py

import chess


class MetricsManager:
    def __init__(self, board_state):
        self.board_state = board_state
        self.metrics = {
            "short_term": {},
            "long_term": {}
        }

    def update_all_metrics(self):
        self.metrics["short_term"]["attacked_squares"] = self.count_attacked_squares()
        self.metrics["short_term"]["defended_pieces"] = self.count_defended_pieces()
        self.metrics["long_term"]["center_control"] = self.evaluate_center_control()
        self.metrics["long_term"]["king_safety"] = self.evaluate_king_safety()
        self.metrics["long_term"]["pawn_structure_stability"] = self.evaluate_pawn_structure()

    def count_attacked_squares(self):
        """Count distinct squares attacked by the side to move."""
        board = self.board_state
        color = board.turn
        attacked = set()
        for square, piece in board.piece_map().items():
            if piece.color == color:
                attacked.update(board.attacks(square))
        return len(attacked)

    def count_defended_pieces(self):
        """Count pieces of the side to move that are defended by a friendly piece."""
        board = self.board_state
        color = board.turn
        defended = 0
        for square, piece in board.piece_map().items():
            if piece.color == color and board.attackers(color, square):
                defended += 1
        return defended

    def evaluate_center_control(self):
        """Evaluate control of the four central squares."""
        board = self.board_state
        color = board.turn
        center = [chess.D4, chess.E4, chess.D5, chess.E5]
        return sum(1 for sq in center if board.is_attacked_by(color, sq))

    def evaluate_king_safety(self):
        """Count safe squares around the king (not attacked by the opponent)."""
        board = self.board_state
        color = board.turn
        king_square = board.king(color)
        if king_square is None:
            return 0
        moves = chess.SquareSet(chess.BB_KING_ATTACKS[king_square])
        return sum(1 for sq in moves if not board.is_attacked_by(not color, sq))

    def evaluate_pawn_structure(self):
        """Return a simple pawn structure score (penalising isolated and doubled pawns)."""
        board = self.board_state
        color = board.turn
        pawns = board.pieces(chess.PAWN, color)
        files = {}
        for sq in pawns:
            file = chess.square_file(sq)
            files.setdefault(file, 0)
            files[file] += 1
        doubled = sum(count - 1 for count in files.values() if count > 1)
        isolated = 0
        for file, count in files.items():
            if not any(f in files for f in (file - 1, file + 1)):
                isolated += count
        return -(doubled + isolated)

    def get_metrics(self):
        return self.metrics


class BoardMetrics:
    """Minimal metrics helper used in tests.

    Only a single metric – ``material_balance`` – is tracked.  The method
    :meth:`update_from_board` relies on :meth:`Board.get_pieces` to avoid direct
    access to the board's internal ``pieces`` list.
    """

    def __init__(self):
        self._metrics = {}

    def update_from_board(self, board, analyzer):  # pragma: no cover - trivial
        white = len(board.get_pieces('white'))
        black = len(board.get_pieces('black'))
        self._metrics['material_balance'] = white - black

    def get_metrics(self):  # pragma: no cover - trivial
        return self._metrics
