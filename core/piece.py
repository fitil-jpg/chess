try:  # Optional dependency used only for advanced piece logic
    import chess  # type: ignore
except Exception:  # pragma: no cover - chess may be absent in tests
    chess = None

from .board import Board


def _color_to_bool(color):
    """Return ``True`` for white and ``False`` for black for various inputs."""

    if isinstance(color, str):
        return color == 'white'
    return bool(color)


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

    def get_attacked_squares(self, board=None, chess_board=None):
        """Return squares this piece attacks using python-chess helpers.

        ``board`` is optional and only used when a pre-built
        :class:`chess.Board` is not supplied via ``chess_board``.  This allows
        callers that already have a python-chess board to avoid rebuilding it
        for every piece, improving performance.
        """

        if chess is None:  # pragma: no cover - defensive fallback
            return set()

        square = self._as_square()
        if square is None:
            return set()

        cb = chess_board
        if cb is None:
            if board is None:
                return set()
            cb = build_chess_board(board)

        return set(cb.attacks(square))

    def get_defended_squares(self, board=None, chess_board=None):
        """Return squares defended by this piece.

        A defended square is one that the piece attacks but is occupied by a
        friendly piece.  The logic mirrors :meth:`get_attacked_squares` while
        filtering out enemy or empty squares.
        """

        if chess is None:  # pragma: no cover - defensive fallback
            return set()

        cb = chess_board
        if cb is None:
            if board is None:
                return set()
            cb = build_chess_board(board)

        defended = set()
        self_color = _color_to_bool(self.color)
        for sq in self.get_attacked_squares(chess_board=cb):
            piece = cb.piece_at(sq)
            if piece and piece.color == self_color:
                defended.add(sq)
        return defended

class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

class Rook(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_defended(self, board=None, chess_board=None):
        """Populate ``defended_moves`` and ``attacked_moves`` overlays."""
        self.defended_moves.clear()
        self.attacked_moves.clear()

        cb = chess_board
        if cb is None:
            if board is None:
                return
            cb = build_chess_board(board)

        for sq in self.get_attacked_squares(chess_board=cb):
            piece = cb.piece_at(sq)
            if piece is None:
                continue
            if piece.color == _color_to_bool(self.color):
                self.defended_moves.add(sq)
            else:
                self.attacked_moves.add(sq)

class Knight(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_fork(self, board=None, chess_board=None):
        cb = chess_board
        if cb is None:
            if board is None:
                return
            cb = build_chess_board(board)
        self.fork_moves.clear()
        fork_targets = []
        for sq in self.get_attacked_squares(chess_board=cb):
            piece = cb.piece_at(sq)
            if piece and piece.color != _color_to_bool(self.color) and piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                fork_targets.append(sq)
        if len(fork_targets) >= 2:
            self.fork_moves.update(fork_targets)

class Bishop(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

class Queen(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_hanging(self, board=None, chess_board=None):
        cb = chess_board
        if cb is None:
            if board is None:
                return
            cb = build_chess_board(board)
        self.hanging_targets.clear()
        for sq in self.get_attacked_squares(chess_board=cb):
            piece = cb.piece_at(sq)
            if piece and piece.color != _color_to_bool(self.color):
                defenders = cb.attackers(not _color_to_bool(self.color), sq)
                if not defenders:
                    self.hanging_targets.add(sq)

    def update_pin_and_check(self, board=None, chess_board=None):
        cb = chess_board
        if cb is None:
            if board is None:
                return
            cb = build_chess_board(board)
        self.pin_moves.clear()
        self.check_squares.clear()
        attacks = self.get_attacked_squares(chess_board=cb)
        queen_sq = self._as_square()
        for sq in attacks:
            piece = cb.piece_at(sq)
            if piece and piece.color != _color_to_bool(self.color) and piece.piece_type != chess.KING:
                ksq = cb.king(not _color_to_bool(self.color))
                if ksq is not None:
                    rq, rf = chess.square_rank(sq), chess.square_file(sq)
                    kr, kf = chess.square_rank(ksq), chess.square_file(ksq)
                    qr, qf = self.position
                    if rq == kr or rf == kf or abs(rq - kr) == abs(rf - kf):
                        self.pin_moves.add(sq)
        king_sq = cb.king(not _color_to_bool(self.color))
        if king_sq and king_sq in attacks:
            self.check_squares.add(king_sq)

class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_king_moves(self, board=None, chess_board=None):
        cb = chess_board
        if cb is None:
            if board is None:
                return
            cb = build_chess_board(board)
        self.safe_moves.clear()
        self.attacked_moves.clear()
        king_sq = self._as_square()
        for move in cb.legal_moves:
            if move.from_square == king_sq:
                attackers = cb.attackers(not _color_to_bool(self.color), move.to_square)
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


def build_chess_board(board):
    """Construct a :class:`chess.Board` from a project board-like object."""

    if chess is None:  # pragma: no cover - chess may be absent in tests
        return None

    if isinstance(board, chess.Board):
        return board

    if hasattr(board, "board") and isinstance(board.board, chess.Board):
        return board.board

    cb = chess.Board()
    cb.clear()
    for piece in board.get_pieces():
        pos = piece.position
        if isinstance(pos, str):
            square = chess.parse_square(pos)
        else:
            r, f = pos
            square = chess.square(f, r)
        color = chess.WHITE if _color_to_bool(piece.color) else chess.BLACK
        if isinstance(piece, Pawn):
            ptype = chess.PAWN
        elif isinstance(piece, Rook):
            ptype = chess.ROOK
        elif isinstance(piece, Knight):
            ptype = chess.KNIGHT
        elif isinstance(piece, Bishop):
            ptype = chess.BISHOP
        elif isinstance(piece, Queen):
            ptype = chess.QUEEN
        elif isinstance(piece, King):
            ptype = chess.KING
        else:
            continue
        cb.set_piece_at(square, chess.Piece(ptype, color))
    return cb

