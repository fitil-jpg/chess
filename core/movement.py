import logging
logger = logging.getLogger(__name__)

class ChessMovement:
    def __init__(self, board):
        self.board = board
        self.selected_piece = None
        self.selected_coords = None

    def on_square_click(self, event):
        col = event.x // 50
        row = event.y // 50
        piece = self.board.board_state[row][col]
        logger.debug(f"Clicked piece is {piece}")

        if piece and self.selected_coords is None:
            self.selected_piece = piece
            self.selected_coords = (col, row)
            logger.debug(f"Selected {piece} at ({col}, {row})")
            self.board.set_selected_square(col, row)
            self.highlight_possible_moves(piece, col, row)

        elif self.selected_coords:
            start_col, start_row = self.selected_coords
            if self.is_valid_move(self.selected_piece, start_col, start_row, col, row):
                self.move_piece(start_col, start_row, col, row)
            self.selected_coords = None
            self.board.clear_selected_square()
            self.board.clear_highlight()

    def is_valid_move(self, piece, start_col, start_row, end_col, end_row):
        dx = end_col - start_col
        dy = end_row - start_row
        
        if "pawn" in piece:
            direction = -1 if "white" in piece else 1
            if start_col == end_col and self.board.board_state[end_row][end_col] is None:
                if end_row == start_row + direction:
                    return True
                if (start_row == 6 and "white" in piece) or (start_row == 1 and "black" in piece):
                    if end_row == start_row + 2 * direction:
                        return True
            if abs(dx) == 1 and dy == direction:
                target = self.board.board_state[end_row][end_col]
                if target and ("white" in piece) != ("white" in target):
                    return True

        elif "knight" in piece:
            return (abs(dx), abs(dy)) in [(1, 2), (2, 1)]

        return False

    def move_piece(self, start_col, start_row, end_col, end_row):
        piece = self.board.board_state[start_row][start_col]
        if piece:
            self.board.remove_piece(start_col, start_row)
            self.board.place_piece(piece, end_col, end_row)
            self.board.board_state[start_row][start_col] = None
            self.board.board_state[end_row][end_col] = piece
            logger.debug(
                f"Moved {piece} from ({start_col}, {start_row}) to ({end_col}, {end_row})"
            )

    def highlight_possible_moves(self, piece, start_col, start_row):
        self.board.clear_highlight()
        directions = []

        if "pawn" in piece:
            direction = -1 if "white" in piece else 1
            for dy in [direction, 2 * direction]:
                end_row = start_row + dy
                if 0 <= end_row < 8:
                    if self.is_valid_move(piece, start_col, start_row, start_col, end_row):
                        self.board.highlight_square(start_col, end_row, color="#DDDDDD")
            for dx in [-1, 1]:
                end_col = start_col + dx
                end_row = start_row + direction
                if 0 <= end_col < 8 and 0 <= end_row < 8:
                    if self.is_valid_move(piece, start_col, start_row, end_col, end_row):
                        self.board.highlight_square(end_col, end_row, color="#DDDDDD")

        elif "knight" in piece:
            knight_moves = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
            for dx, dy in knight_moves:
                x = start_col + dx
                y = start_row + dy
                if 0 <= x < 8 and 0 <= y < 8:
                    if self.is_valid_move(piece, start_col, start_row, x, y):
                        self.board.highlight_square(x, y, color="#DDDDDD")