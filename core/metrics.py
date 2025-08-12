# metrics.py

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
        return 0  # TODO

    def count_defended_pieces(self):
        return 0  # TODO

    def evaluate_center_control(self):
        return 0  # TODO

    def evaluate_king_safety(self):
        return 0  # TODO

    def evaluate_pawn_structure(self):
        return 0  # TODO

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
