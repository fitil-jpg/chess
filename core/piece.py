try:  # Optional dependency used only for advanced piece logic
    import chess  # type: ignore
except Exception:  # pragma: no cover - chess may be absent in tests
    chess = None


def _parse_position(pos):
    """Return the python-chess square index for ``pos``.

    ``pos`` may be either an ``(rank, file)`` tuple (0-indexed) or the
    traditional string notation like ``"e2"`` used throughout the tests.
    """
    if chess is None:
        return None
    if isinstance(pos, str):
        return chess.parse_square(pos)
    if isinstance(pos, tuple) and len(pos) == 2:
        rank, file = pos
        return chess.square(file, rank)
    return None


class Piece:
    def __init__(self, color, position):
        self.color = color
        self.position = position  # typically 'e2' or (rank, file)
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

    # --- helpers ---------------------------------------------------------
    def _square(self):
        return _parse_position(self.position)

    def _color(self):
        if chess is None:
            return None
        if isinstance(self.color, str):
            return chess.WHITE if self.color == 'white' else chess.BLACK
        # Assume boolean from python-chess: True -> white
        return chess.WHITE if self.color else chess.BLACK

    @staticmethod
    def _build_board(board):
        """Create a python-chess board mirroring ``board``.

        The project uses lightweight piece objects without move generation.
        For attack/defense calculations we temporarily translate them into a
        :class:`chess.Board` instance.
        """
        if chess is None:
            return None

        cb = chess.Board.empty()
        for p in board.get_pieces():
            sq = _parse_position(p.position)
            piece_type = PIECE_TYPE_MAP.get(type(p))
            if sq is not None and piece_type is not None:
                cb.set_piece_at(sq, chess.Piece(piece_type, chess.WHITE if p.color == 'white' else chess.BLACK))
        return cb

    # --- public API ------------------------------------------------------
    def get_attacked_squares(self, board):
        """Return squares this piece attacks.

        The original project only needed a placeholder.  For this kata we
        leverage :mod:`python-chess` to compute the real attack set whenever
        the dependency is available.  Squares are returned using standard
        algebraic notation like ``"e4"`` so that callers can work with a
        human friendly representation.
        """
        if chess is None:
            return set()
        cb = self._build_board(board)
        sq = self._square()
        if cb is None or sq is None:
            return set()
        return {chess.square_name(t) for t in cb.attacks(sq)}

    def get_defended_squares(self, board):
        """Return squares occupied by friendly pieces that this piece protects."""
        if chess is None:
            return set()
        cb = self._build_board(board)
        sq = self._square()
        color = self._color()
        if cb is None or sq is None or color is None:
            return set()

        defended = set()
        for target in cb.attacks(sq):
            piece = cb.piece_at(target)
            if piece and piece.color == color:
                defended.add(chess.square_name(target))
        return defended

class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

class Rook(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_defended(self, board):
        self.defended_moves.clear()
        rook_sq = self._square()
        if rook_sq is None:
            return
        for sq in board.attacks(rook_sq):
            piece = board.piece_at(sq)
            if piece and piece.color == self._color():
                self.defended_moves.add(sq)

class Knight(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_fork(self, board):
        self.fork_moves.clear()
        knight_sq = self._square()
        if knight_sq is None:
            return
        fork_targets = []
        for sq in board.attacks(knight_sq):
            piece = board.piece_at(sq)
            if piece and piece.color != self._color() and piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
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
        queen_sq = self._square()
        if queen_sq is None:
            return
        for sq in board.attacks(queen_sq):
            piece = board.piece_at(sq)
            if piece and piece.color != self._color():
                defenders = board.attackers(not self._color(), sq)
                if not defenders:
                    self.hanging_targets.add(sq)
    def update_pin_and_check(self, board):
        self.pin_moves.clear()
        self.check_squares.clear()
        queen_sq = self._square()
        if queen_sq is None:
            return
        for sq in board.attacks(queen_sq):
            piece = board.piece_at(sq)
            if piece and piece.color != self._color() and piece.piece_type != chess.KING:
                ksq = board.king(not self._color())
                if ksq is not None:
                    rq, rf = chess.square_rank(sq), chess.square_file(sq)
                    kr, kf = chess.square_rank(ksq), chess.square_file(ksq)
                    qr, qf = chess.square_rank(queen_sq), chess.square_file(queen_sq)
                    if rq == kr or rf == kf or abs(rq - kr) == abs(rf - kf):
                        self.pin_moves.add(sq)
            king_sq = board.king(not self._color())
            if king_sq and king_sq in board.attacks(queen_sq):
                self.check_squares.add(king_sq)

class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_king_moves(self, board):
        self.safe_moves.clear()
        self.attacked_moves.clear()
        king_sq = self._square()
        if king_sq is None:
            return
        for move in board.legal_moves:
            if move.from_square == king_sq:
                attackers = board.attackers(not self._color(), move.to_square)
                if attackers:
                    self.attacked_moves.add(move.to_square)
                else:
                    self.safe_moves.add(move.to_square)

if chess:
    PIECE_TYPE_MAP = {
        Pawn: chess.PAWN,
        Rook: chess.ROOK,
        Knight: chess.KNIGHT,
        Bishop: chess.BISHOP,
        Queen: chess.QUEEN,
        King: chess.KING,
    }
else:  # pragma: no cover - chess not available
    PIECE_TYPE_MAP = {}

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

