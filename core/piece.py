try:  # Optional dependency used only for advanced piece logic
    import chess  # type: ignore
except Exception:  # pragma: no cover - chess may be absent in tests
    chess = None

from .board import Board


def _color_to_str(color):
    """Return ``'white'`` or ``'black'`` for various color representations."""

    if isinstance(color, str):
        return color
    return 'white' if color else 'black'

class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position  # (rank, file)
        self.moves_made = 0
        self.squares_crossed = 0
        self.targets_attacked = 0
        self.attacked_pieces = []
        self.total_targets_attacked = 0
        self.unprotected_targets = []
        self.life_history = []
        self.strategic_weight = 1.0
        # DrawerManager overlays:
        self.safe_moves = set()
        self.attacked_moves = set()
        self.defended_moves = set()
        self.fork_moves = set()
        self.hanging_targets = set()
        self.pin_moves = set()
        self.check_squares = set()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _as_square(self):
        """Return the python-chess ``square`` index for ``self.position``.

        The ``position`` attribute stores coordinates as ``(rank, file)`` to
        match the project's convention.  python-chess, however, expects a
        single square index.  This helper performs the conversion so that
        higher level methods can simply work with the returned square.  If the
        optional :mod:`chess` dependency is missing the function returns
        ``None`` which signals callers to fall back to defensive defaults.
        """

        if chess is None:  # pragma: no cover - chess may be absent in tests
            return None

        rank, file = self.position
        return chess.square(file, rank)

    def get_attacked_squares(self, board):
        """Return squares this piece attacks using python-chess helpers."""

        if chess is None:  # pragma: no cover - defensive fallback
            return set()

        square = self._as_square()
        if square is None:
            return set()

        # ``board.attacks`` is provided by python-chess; for custom board
        # implementations the method is expected to mirror this behaviour.
        return set(board.attacks(square))

    def get_defended_squares(self, board):
        """Return squares defended by this piece.

        A defended square is one that the piece attacks but is occupied by a
        friendly piece.  The logic mirrors :meth:`get_attacked_squares` while
        filtering out enemy or empty squares.
        """

        if chess is None:  # pragma: no cover - defensive fallback
            return set()

        defended = set()
        for sq in self.get_attacked_squares(board):
            piece = board.piece_at(sq)
            if piece and piece.color == self.color:
                defended.add(sq)
        return defended

class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

class Rook(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_defended(self, board):
        """Populate ``defended_moves`` and ``attacked_moves`` overlays."""
        self.defended_moves.clear()
        self.attacked_moves.clear()

        for sq in self.get_attacked_squares(board):
            piece = board.piece_at(sq)
            if piece is None:
                continue
            if piece.color == self.color:
                self.defended_moves.add(sq)
            else:
                self.attacked_moves.add(sq)

class Knight(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_fork(self, board):
        self.fork_moves.clear()
        fork_targets = []
        for sq in self.get_attacked_squares(board):
            piece = board.piece_at(sq)
            if piece and piece.color != self.color and piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                fork_targets.append(sq)
        if len(fork_targets) >= 2:
            self.fork_moves.update(fork_targets)

class Bishop(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

class Queen(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_hanging(self, board):
        self.hanging_targets.clear()
        for sq in self.get_attacked_squares(board):
            piece = board.piece_at(sq)
            if piece and piece.color != self.color:
                defenders = board.attackers(not self.color, sq)
                if not defenders:
                    self.hanging_targets.add(sq)
    def update_pin_and_check(self, board):
        self.pin_moves.clear()
        self.check_squares.clear()
        attacks = self.get_attacked_squares(board)
        queen_sq = self._as_square()
        for sq in attacks:
            piece = board.piece_at(sq)
            if piece and piece.color != self.color and piece.piece_type != chess.KING:
                ksq = board.king(not self.color)
                if ksq is not None:
                    rq, rf = chess.square_rank(sq), chess.square_file(sq)
                    kr, kf = chess.square_rank(ksq), chess.square_file(ksq)
                    qr, qf = self.position
                    if rq == kr or rf == kf or abs(rq - kr) == abs(rf - kf):
                        self.pin_moves.add(sq)
        king_sq = board.king(not self.color)
        if king_sq and king_sq in attacks:
            self.check_squares.add(king_sq)

class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_king_moves(self, board):
        self.safe_moves.clear()
        self.attacked_moves.clear()
        king_sq = self._as_square()
        for move in board.legal_moves:
            if move.from_square == king_sq:
                attackers = board.attackers(not self.color, move.to_square)
                if attackers:
                    self.attacked_moves.add(move.to_square)
                else:
                    self.safe_moves.add(move.to_square)

def piece_class_factory(piece, pos):
    t = piece.symbol().lower()
    if t == 'p':
        return Pawn(piece.color, pos)
    elif t == 'r':
        return Rook(piece.color, pos)
    elif t == 'n':
        return Knight(piece.color, pos)
    elif t == 'b':
        return Bishop(piece.color, pos)
    elif t == 'q':
        return Queen(piece.color, pos)
    elif t == 'k':
        return King(piece.color, pos)
    return Piece(piece.color, pos)


def _build_board(chess_board):
    """Construct a project :class:`Board` from a python-chess board."""

    board = Board()
    if chess is None:  # pragma: no cover - python-chess is optional
        return board

    for square, p in chess_board.piece_map().items():
        pos = (chess.square_rank(square), chess.square_file(square))
        piece = piece_class_factory(p, pos)
        piece.color = _color_to_str(piece.color)
        board.place_piece(piece)

    return board

