import chess

def piece_value(piece):
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
              chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
    return values.get(piece.piece_type, 0)

class Evaluator:
    def __init__(self, board):
        self.board = board
        # last recorded mobility stats: {'white': int, 'black': int, 'score': int}
        self.mobility_stats = {"white": 0, "black": 0, "score": 0}

    def mobility(self, board=None):
        """Return a tuple with number of legal moves for white and black.

        The board's ``turn`` attribute is temporarily flipped to count the
        opponent's moves.  Results are stored in ``self.mobility_stats`` for
        telemetry purposes.
        """
        board = board or self.board
        orig_turn = board.turn
        white_moves = len(board.legal_moves)
        board.turn = not board.turn
        black_moves = len(board.legal_moves)
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

    # --- Lightweight helpers used by DynamicBot ---
    def material_diff(self, color: bool) -> int:
        """Return material difference from ``color``'s point of view."""
        return self.material_count(color) - self.material_count(not color)

    def king_safety(self, color: bool) -> int:
        """Simple king safety metric: defenders minus attackers."""
        board = self.board
        king_sq = board.king(color)
        if king_sq is None:
            return 0
        attackers = len(board.attackers(not color, king_sq))
        defenders = len(board.attackers(color, king_sq))
        return defenders - attackers

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
