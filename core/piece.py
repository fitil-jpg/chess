try:  # Optional dependency used only for advanced piece logic
    import chess  # type: ignore
except Exception:  # pragma: no cover - chess may be absent in tests
    chess = None

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
    # Utility helpers
    # ------------------------------------------------------------------
    def _as_square(self, pos=None):
        """Return ``pos`` as a python-chess square index.

        ``pos`` defaults to ``self.position`` and may be expressed either as a
        ``(rank, file)`` tuple (0-indexed, matching :mod:`python-chess`) or as a
        standard algebraic string such as ``"e4"``.  ``None`` is returned if the
        :mod:`chess` dependency is unavailable or the position cannot be
        converted.  This keeps the rest of the logic independent from how a
        piece stores its location.
        """

        if chess is None:  # pragma: no cover - ``chess`` optional in tests
            return None

        pos = self.position if pos is None else pos

        if isinstance(pos, int):  # already a square index
            return pos

        if isinstance(pos, str):
            try:
                return chess.parse_square(pos)
            except Exception:  # pragma: no cover - defensive
                return None

        # Expect an (rank, file) tuple
        try:
            rank, file = pos
        except Exception:  # pragma: no cover - malformed input
            return None
        return chess.square(file, rank)

    def get_attacked_squares(self, board):
        """Return squares this piece attacks using python-chess helpers."""

        if chess is None or not hasattr(board, "attacks"):
            return set()  # pragma: no cover - defensive fallback

        square = self._as_square()
        if square is None:
            return set()

        return set(board.attacks(square))

    def get_defended_squares(self, board):
        """Return squares defended by this piece.

        A defended square is one that the piece attacks but is occupied by a
        friendly piece.  The logic mirrors :meth:`get_attacked_squares` while
        filtering out enemy or empty squares.
        """

        if chess is None or not hasattr(board, "piece_at"):
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

        attacked = self.get_attacked_squares(board)
        defended = self.get_defended_squares(board)
        self.defended_moves.update(defended)
        self.attacked_moves.update(attacked - defended)

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

