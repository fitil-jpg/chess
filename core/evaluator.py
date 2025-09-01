import logging
logger = logging.getLogger(__name__)

import chess
from .pst_trainer import PST
from .phase import GamePhaseDetector

def piece_value(piece):
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
              chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    return values.get(piece.piece_type, 0)


def escape_squares(board: chess.Board, square: int) -> set[chess.Move]:
    """Return the set of safe moves for the piece on ``square``.

    A move is considered an "escape" if after making it the piece is not
    attacked by the opponent.  The original ``board.turn`` is restored when
    finished so the function is side-effect free for callers.
    """

    piece = board.piece_at(square)
    if piece is None:
        return set()

    orig_turn = board.turn
    board.turn = piece.color
    escapes: set[chess.Move] = set()
    for mv in board.legal_moves:
        if mv.from_square != square:
            continue
        board.push(mv)
        if not board.is_attacked_by(not piece.color, mv.to_square):
            escapes.add(mv)
        board.pop()
    board.turn = orig_turn
    return escapes


def is_piece_mated(board: chess.Board, square: int) -> bool:
    """Return ``True`` if the piece on ``square`` is attacked with no escape.

    A piece is considered *mated* if the opponent currently attacks its
    square and :func:`escape_squares` finds no legal moves that leave the piece
    safe.  The function is side‑effect free with respect to ``board.turn``.
    """

    piece = board.piece_at(square)
    if piece is None:
        return False

    if not board.is_attacked_by(not piece.color, square):
        return False

    return len(escape_squares(board, square)) == 0

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

        # last recorded mobility stats:
        # {
        #   'white': {'pieces': {sq: {'mobility': int,
        #                             'blocked': bool,
        #                             'capturable': bool,
        #                             'status': str | None}},
        #             'blocked': int, 'capturable': int, 'total': int},
        #   'black': {...},
        #   'score': int
        # }
        self.mobility_stats = {
            "white": {"pieces": {}, "blocked": 0, "capturable": 0, "total": 0},
            "black": {"pieces": {}, "blocked": 0, "capturable": 0, "total": 0},
            "score": 0,
        }

    @staticmethod
    def piece_zone(board: chess.Board, square: int, radius: int) -> set[int]:
        """Return squares around ``square`` relevant for piece safety.

        The shape of the returned zone depends on the piece type located on
        ``square``:

        * King and most pieces use a simple circle based on
          :func:`chess.square_distance`.
        * Knights also use a circular zone but callers typically pass a larger
          ``radius`` (e.g. ``2``).
        * Queens expand along ranks, files and diagonals up to ``radius``
          squares, forming an "intersection of lines".
        """

        piece = board.piece_at(square)
        if piece is None:
            return set()

        zone: set[int] = set()

        file = chess.square_file(square)
        rank = chess.square_rank(square)

        if piece.piece_type == chess.QUEEN:
            directions = [
                (1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1),
            ]
            for df, dr in directions:
                for dist in range(1, radius + 1):
                    f = file + df * dist
                    r = rank + dr * dist
                    if 0 <= f < 8 and 0 <= r < 8:
                        zone.add(chess.square(f, r))
        else:
            for sq in chess.SQUARES:
                if chess.square_distance(square, sq) <= radius:
                    zone.add(sq)

        return zone

    def mobility(self, board=None):
        """Return total mobility for white and black.

        Mobility is calculated per piece to determine whether a piece is
        ``blocked`` (no legal moves) or ``capturable`` (attacked by the
        opponent).  The king receives dedicated handling so that checkmate and
        stalemate are labelled separately from ordinary blocking.  Totals are
        adjusted by penalising blocked or capturable pieces to reflect reduced
        mobility.  Detailed per-piece statistics are stored in
        ``self.mobility_stats``.
        """
        board = board or self.board
        orig_turn = board.turn

        stats = {
            chess.WHITE: {"pieces": {}, "blocked": 0, "capturable": 0, "total": 0},
            chess.BLACK: {"pieces": {}, "blocked": 0, "capturable": 0, "total": 0},
        }

        for color in (chess.WHITE, chess.BLACK):
            board.turn = color
            all_moves = list(board.legal_moves)
            move_counts: dict[int, int] = {}
            for mv in all_moves:
                move_counts[mv.from_square] = move_counts.get(mv.from_square, 0) + 1

            for sq, piece in board.piece_map().items():
                if piece.color != color:
                    continue

                move_count = move_counts.get(sq, 0)
                capturable = board.is_attacked_by(not color, sq)
                blocked = move_count == 0
                status = None

                if piece.piece_type == chess.KING:
                    if board.is_checkmate():
                        status = "checkmated"
                    elif board.is_stalemate():
                        status = "stalemated"
                    else:
                        status = "blocked" if blocked else "mobile"

                stats[color]["pieces"][sq] = {
                    "mobility": move_count,
                    "blocked": blocked,
                    "capturable": capturable,
                    "status": status,
                }

                if blocked:
                    stats[color]["blocked"] += 1
                if capturable:
                    stats[color]["capturable"] += 1

                contribution = move_count
                if blocked:
                    contribution -= 1
                if capturable:
                    contribution -= 1
                stats[color]["total"] += max(contribution, 0)

        board.turn = orig_turn

        white_total = stats[chess.WHITE]["total"]
        black_total = stats[chess.BLACK]["total"]
        score = white_total - black_total
        self.mobility_stats = {
            "white": stats[chess.WHITE],
            "black": stats[chess.BLACK],
            "score": score,
        }
        return white_total, black_total

    def criticality(self, board: chess.Board | None = None, color: bool | None = None):
        """Return a list of opponent pieces ordered by their threat level.

        Each opponent piece receives a score based on its proximity to our
        king and, for knights, whether it can deliver a fork on the king and an
        important piece (queen or rook) within two moves.  The result is a list
        of ``(square, score)`` tuples sorted by descending ``score``.
        """

        board = board or self.board
        color = board.turn if color is None else color
        enemy = not color

        king_sq = board.king(color)
        # Squares of our most valuable pieces that we care about for forks
        important: list[int] = [
            sq
            for sq, p in board.piece_map().items()
            if p.color == color and p.piece_type in (chess.QUEEN, chess.ROOK)
        ]

        critical: list[tuple[int, int]] = []
        for sq, piece in board.piece_map().items():
            if piece.color != enemy:
                continue

            score = 0
            if king_sq is not None:
                dist = chess.square_distance(sq, king_sq)
                score += max(0, 7 - dist)

            # Detect potential knight forks up to two moves away
            if (
                piece.piece_type == chess.KNIGHT
                and king_sq is not None
                and important
            ):
                attacks1 = chess.SquareSet(chess.BB_KNIGHT_ATTACKS[sq])
                fork_found = False
                for inter in attacks1:
                    attacks2 = chess.SquareSet(chess.BB_KNIGHT_ATTACKS[inter])
                    for final in attacks2:
                        attack_set = chess.SquareSet(
                            chess.BB_KNIGHT_ATTACKS[final]
                        )
                        if king_sq in attack_set and any(
                            imp in attack_set for imp in important
                        ):
                            fork_found = True
                            break
                    if fork_found:
                        break
                if fork_found:
                    score += 10

            if score > 0:
                critical.append((sq, score))

        critical.sort(key=lambda x: x[1], reverse=True)
        return critical

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
        result['white_blocked'] = self.mobility_stats['white']['blocked']
        result['black_blocked'] = self.mobility_stats['black']['blocked']
        result['white_capturable'] = self.mobility_stats['white']['capturable']
        result['black_capturable'] = self.mobility_stats['black']['capturable']
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