import chess

class DrawerManager:
    def __init__(self):
        self.overlays = {}

    def collect_overlays(self, piece_objects, board):
        self.overlays.clear()
        for sq, obj in piece_objects.items():
            if hasattr(obj, "safe_moves"):
                for s in obj.safe_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "king_safe", "white" if obj.color else "black")
            if hasattr(obj, "attacked_moves"):
                for s in obj.attacked_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "king_attacked", "red")
            if hasattr(obj, "defended_moves"):
                for s in obj.defended_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "rook_defended", "blue")
            if hasattr(obj, "fork_moves"):
                for s in obj.fork_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "knight_fork", "magenta")
            if hasattr(obj, "hanging_targets"):
                for s in obj.hanging_targets:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "queen_hanging", "orange")
            if hasattr(obj, "pin_moves"):
                for s in obj.pin_moves:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "pin", "cyan")
            if hasattr(obj, "check_squares"):
                for s in obj.check_squares:
                    row = 7 - chess.square_rank(s)
                    col = chess.square_file(s)
                    self._add_overlay(row, col, "check", "yellow")

    def _add_overlay(self, row, col, overlay_type, color):
        if (row, col) not in self.overlays:
            self.overlays[(row, col)] = []
        self.overlays[(row, col)].append((overlay_type, color))

    def get_cell_overlays(self, row, col):
        return self.overlays.get((row, col), [])
