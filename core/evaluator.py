import chess
from .pst_trainer import PST
from .phase import GamePhaseDetector

def piece_value(piece):
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
              chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    return values.get(piece.piece_type, 0)

class Evaluator:
    def __init__(
        self,
        board: chess.Board,
        isolated_penalty: int = -10,
        doubled_penalty: int = -5,
        passed_bonus: int = 20,
    ):
        """Create a new :class:`Evaluator` for ``board``.

        Parameters are optional tuning knobs for pawn-structure evaluation.
        ``isolated_penalty`` and ``doubled_penalty`` are applied per pawn while
        ``passed_bonus`` rewards passed pawns.  The defaults mirror the
        previously hardcoded constants so existing callers need not change.
        """

        self.board = board
        self.isolated_penalty = isolated_penalty
        self.doubled_penalty = doubled_penalty
        self.passed_bonus = passed_bonus

        # last recorded mobility stats: {'white': int, 'black': int, 'score': int}
        self.mobility_stats = {"white": 0, "black": 0, "score": 0}

    def mobility(self, board=None):
        """Return a tuple with number of legal moves for white and black.

        Counts moves via ``board.legal_moves.count()`` when available so the
        generator is not materialized.  Falls back to ``sum(1 for _ in
        board.legal_moves)`` if ``count()`` is unsupported (e.g. when tests
        replace ``legal_moves`` with a plain iterator).  The board's ``turn``
        attribute is temporarily flipped to count the opponent's moves, and
        results are stored in ``self.mobility_stats`` for telemetry purposes.
        """
        board = board or self.board
        orig_turn = board.turn
        # Use ``count()`` instead of ``len()`` because ``legal_moves`` is a
        # generator.  If ``count()`` is unavailable or requires an argument
        # (like on plain lists), fall back to summing over the iterator.
        moves = board.legal_moves
        try:
            white_moves = moves.count()
        except (AttributeError, TypeError):
            white_moves = sum(1 for _ in moves)
        board.turn = not board.turn
        moves = board.legal_moves
        try:
            black_moves = moves.count()
        except (AttributeError, TypeError):
            black_moves = sum(1 for _ in moves)
        board.turn = orig_turn
        score = white_moves - black_moves
        self.mobility_stats = {"white": white_moves, "black": black_moves, "score": score}
        return white_moves, black_moves

    def compute_features(self, color):
        board = self.board
        features = {}

        # Чи під атакою твій король?
        king_sq = board.king(color)
        features["king_under_attack"] = bool(king_sq and board.is_attacked_by(not color, king_sq))

        # Можна дати шах? (через push/pop)
        features["can_give_check"] = False
        for move in board.legal_moves:
            if board.piece_at(move.from_square) and board.piece_at(move.from_square).color == color:
                board.push(move)
                if board.is_check():
                    features["can_give_check"] = True
                board.pop()
                if features["can_give_check"]:
                    break

        # Є підвішена фігура супротивника? (немає захисників)
        features["has_hanging_enemy"] = False
        features["valuable_capture"] = False

        for move in board.legal_moves:
            tgt = board.piece_at(move.to_square)
            if tgt and tgt.color != color:
                defenders = board.attackers(not color, move.to_square)
                if not defenders:
                    features["has_hanging_enemy"] = True
                if piece_value(tgt) >= 5:  # цінна фігура
                    features["valuable_capture"] = True
        return features

    def compute_final_metrics(self):
        board = self.board
        result = {}
        for color, label in [(chess.WHITE, 'white'), (chess.BLACK, 'black')]:
            king_sq = board.king(color)
            if king_sq is not None:
                attackers = list(board.attackers(not color, king_sq))
                defenders = list(board.attackers(color, king_sq))
                guard_count = 0
                for sq in chess.SQUARES:
                    piece = board.piece_at(sq)
                    if piece and piece.color == color and piece.piece_type != chess.KING:
                        if king_sq in board.attacks(sq):
                            guard_count += 1
                enemy_defended = 0
                for sq in chess.SQUARES:
                    piece = board.piece_at(sq)
                    if piece and piece.color != color:
                        defenders2 = board.attackers(not color, sq)
                        if len(defenders2) > 0:
                            enemy_defended += 1
                result[f'{label}_king_attacked_by'] = len(attackers)
                result[f'{label}_king_defended_by'] = len(defenders)
                result[f'{label}_king_guarded_by'] = guard_count
                result[f'{label}_enemy_pieces_defended'] = enemy_defended
                # Матеріал
                result[f'{label}_material'] = self.material_count(color)
                # Підвіси (всі свої фігури, які атакує противник і не захищає жодна своя)
                hanging = 0
                for sq in chess.SQUARES:
                    piece = board.piece_at(sq)
                    if piece and piece.color == color and piece.piece_type != chess.KING:
                        if board.attackers(not color, sq) and not board.attackers(color, sq):
                            hanging += 1
                result[f'{label}_hanging_pieces'] = hanging
            else:
                result[f'{label}_king_attacked_by'] = None
                result[f'{label}_king_defended_by'] = None
                result[f'{label}_king_guarded_by'] = None
                result[f'{label}_enemy_pieces_defended'] = None
                result[f'{label}_material'] = None
                result[f'{label}_hanging_pieces'] = None
        # Mobility metrics
        white_mob, black_mob = self.mobility(board)
        result['white_mobility'] = white_mob
        result['black_mobility'] = black_mob
        result['mobility_score'] = white_mob - black_mob
        result['position_score'] = self.position_score()
        result['is_checkmate'] = board.is_checkmate()
        result['winner'] = "white" if board.result() == "1-0" else "black" if board.result() == "0-1" else "draw"
        result['moves'] = [m.uci() for m in board.move_stack]
        result['result'] = board.result()
        result['incident_tags'] = game_incident_tags(board)
        return result

    def material_count(self, color):
        score = 0
        values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        for sq in chess.SQUARES:
            p = self.board.piece_at(sq)
            if p and p.color == color:
                score += values.get(p.piece_type, 0)
        return score

    def piece_square_score(self) -> int:
        """Return piece-square table score from White's perspective."""
        phase = GamePhaseDetector.detect(self.board)
        phase_pst = PST["phases"].get(phase, {})
        score = 0
        for sq, piece in self.board.piece_map().items():
            sym = piece.symbol().upper()
            table = phase_pst.get(sym)
            if table is None:
                continue
            idx = sq if piece.color == chess.WHITE else chess.square_mirror(sq)
            val = table[idx]
            if piece.color == chess.WHITE:
                score += val
            else:
                score -= val
        return score

    # --- Pawn structure evaluation -----------------------------------------
    def _is_passed_pawn(self, sq: int, color: bool, enemy_pawns: list[int]) -> bool:
        """Return ``True`` if the pawn on ``sq`` is passed for ``color``."""

        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        for ep in enemy_pawns:
            ef = chess.square_file(ep)
            er = chess.square_rank(ep)
            if abs(ef - file) <= 1:
                if color == chess.WHITE and er > rank:
                    return False
                if color == chess.BLACK and er < rank:
                    return False
        return True

    def pawn_structure_score(self) -> int:
        """Return pawn-structure score from White's perspective."""

        board = self.board
        pawns_by_color: dict[bool, list[int]] = {chess.WHITE: [], chess.BLACK: []}
        for sq, piece in board.piece_map().items():
            if piece.piece_type == chess.PAWN:
                pawns_by_color[piece.color].append(sq)

        score = 0
        for color in (chess.WHITE, chess.BLACK):
            ours = pawns_by_color[color]
            files: dict[int, list[int]] = {}
            for sq in ours:
                files.setdefault(chess.square_file(sq), []).append(sq)

            # doubled pawns
            for fsqs in files.values():
                if len(fsqs) > 1:
                    penalty = self.doubled_penalty * (len(fsqs) - 1)
                    score += penalty if color == chess.WHITE else -penalty

            # isolated / passed
            enemy = pawns_by_color[not color]
            for sq in ours:
                file = chess.square_file(sq)
                has_adjacent = False
                for adj in (file - 1, file + 1):
                    if 0 <= adj < 8 and adj in files and files[adj]:
                        has_adjacent = True
                        break
                if not has_adjacent:
                    penalty = self.isolated_penalty
                    score += penalty if color == chess.WHITE else -penalty

                if self._is_passed_pawn(sq, color, enemy):
                    bonus = self.passed_bonus
                    score += bonus if color == chess.WHITE else -bonus

        return score

    def position_score(self, board: chess.Board | None = None, color: bool | None = None) -> int:
        """Return a lightweight evaluation of ``board`` from ``color``'s perspective.

        The score combines material difference and piece-square table value.  A
        positive score favours ``color``.  If ``board`` is omitted, the
        evaluator's own board is used.  This helper intentionally remains
        simple—sophisticated evaluation is beyond the scope of these tests.
        """

        board = board or self.board
        color = board.turn if color is None else color

        # Temporarily switch the internal board to reuse existing helpers.
        orig = self.board
        self.board = board

        material = self.material_diff(color)
        psq = self.piece_square_score()
        pawn = self.pawn_structure_score()

        # Restore original board state.
        self.board = orig

        return material + psq + pawn if color == chess.WHITE else material - psq - pawn

    # --- Lightweight helpers used by DynamicBot ---
    def material_diff(self, color: bool) -> int:
        """Return material difference from ``color``'s point of view."""
        return self.material_count(color) - self.material_count(not color)

    @staticmethod
    def king_safety(board: chess.Board, color: bool) -> int:
        """Return a simple king safety score for ``color``.

        The score penalizes missing pawn shield squares directly in front of
        the king as well as nearby enemy attackers.  A smaller (possibly
        negative) score indicates a more vulnerable king.
        """
        king_sq = board.king(color)
        if king_sq is None:
            return 0

        file = chess.square_file(king_sq)
        rank = chess.square_rank(king_sq)

        # --- Pawn shield check -------------------------------------------------
        shield_rank = rank + (1 if color == chess.WHITE else -1)
        missing_pawns = 0
        if 0 <= shield_rank < 8:
            for df in (-1, 0, 1):
                f = file + df
                if 0 <= f < 8:
                    sq = chess.square(f, shield_rank)
                    piece = board.piece_at(sq)
                    if not (piece and piece.piece_type == chess.PAWN and piece.color == color):
                        missing_pawns += 1

        # --- Enemy attackers near the king ------------------------------------
        attackers: set[int] = set()
        for df in range(-2, 3):
            for dr in range(-2, 3):
                f = file + df
                r = rank + dr
                if 0 <= f < 8 and 0 <= r < 8:
                    sq = chess.square(f, r)
                    attackers.update(board.attackers(not color, sq))
        for df in range(-3, 4):
            for dr in range(-3, 4):
                if max(abs(df), abs(dr)) == 3:
                    f = file + df
                    r = rank + dr
                    if 0 <= f < 8 and 0 <= r < 8:
                        sq = chess.square(f, r)
                        attackers.update(board.attackers(not color, sq))

        attackers_count = len(attackers)

        # Less pawns and more attackers reduce the score.
        king_safety_score = 0 - missing_pawns - attackers_count
        return king_safety_score

def game_incident_tags(board):
    tags = []
    material = get_material(board)
    # Втрата ферзя:
    if material['white']['Q'] == 0:
        tags.append("lost_queen_white")
    if material['black']['Q'] == 0:
        tags.append("lost_queen_black")
    # Bare king:
    for color in ('white', 'black'):
        pieces = sum(material[color].values()) - material[color]['K']
        if pieces == 0:
            tags.append(f"bare_king_{color}")
    # Матування простим пішаком/конем
    if board.is_checkmate() and board.move_stack:
        last_move = board.move_stack[-1]
        piece = board.piece_at(last_move.to_square)
        if piece and piece.piece_type in [chess.PAWN, chess.KNIGHT]:
            tags.append(f"mated_by_{piece.symbol().lower()}")
    return tags

def get_material(board):
    d = {'white': {'K': 0, 'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'P': 0}, 'black': {'K': 0, 'Q': 0, 'R': 0, 'B': 0, 'N': 0, 'P': 0}}
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            color = 'white' if p.color == chess.WHITE else 'black'
            sym = p.symbol().upper()
            d[color][sym] += 1
    return d
