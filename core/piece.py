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

    def get_attacked_squares(self, board):
        """Return squares this piece attacks.

        The project currently does not model real chess movement, so this
        placeholder simply returns an empty set.  It allows other modules –
        notably :class:`BoardAnalyzer` – to query attack information without
        raising ``AttributeError``.
        """
        return set()

class Pawn(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)

class Rook(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_defended(self, board):
        self.defended_moves.clear()
        rook_sq = chess.square(self.position[1], self.position[0])
        for sq in board.attacks(rook_sq):
            piece = board.piece_at(sq)
            if piece and piece.color == self.color:
                self.defended_moves.add(sq)

class Knight(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_fork(self, board):
        self.fork_moves.clear()
        knight_sq = chess.square(self.position[1], self.position[0])
        fork_targets = []
        for sq in board.attacks(knight_sq):
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
        queen_sq = chess.square(self.position[1], self.position[0])
        for sq in board.attacks(queen_sq):
            piece = board.piece_at(sq)
            if piece and piece.color != self.color:
                defenders = board.attackers(not self.color, sq)
                if not defenders:
                    self.hanging_targets.add(sq)
    def update_pin_and_check(self, board):
        self.pin_moves.clear()
        self.check_squares.clear()
        queen_sq = chess.square(self.position[1], self.position[0])
        for sq in board.attacks(queen_sq):
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
            if king_sq and king_sq in board.attacks(queen_sq):
                self.check_squares.add(king_sq)

class King(Piece):
    def __init__(self, color, position):
        super().__init__(color, position)
    def update_king_moves(self, board):
        self.safe_moves.clear()
        self.attacked_moves.clear()
        king_sq = chess.square(self.position[1], self.position[0])
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
