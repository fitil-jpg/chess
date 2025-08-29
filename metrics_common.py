from __future__ import annotations

import chess


def count_attacked_squares(board: chess.Board) -> int:
    """Return the difference in attacked squares (white - black)."""
    white_attacks: chess.SquareSet = chess.SquareSet()
    black_attacks: chess.SquareSet = chess.SquareSet()
    for sq, piece in board.piece_map().items():
        if piece.color == chess.WHITE:
            white_attacks |= board.attacks(sq)
        else:
            black_attacks |= board.attacks(sq)
    return len(white_attacks) - len(black_attacks)


def count_defended_pieces(board: chess.Board) -> int:
    """Return the difference in defended pieces (white - black)."""
    white_defended = 0
    black_defended = 0
    for sq, piece in board.piece_map().items():
        if board.attackers(piece.color, sq):
            if piece.color == chess.WHITE:
                white_defended += 1
            else:
                black_defended += 1
    return white_defended - black_defended


def evaluate_center_control(board: chess.Board) -> int:
    """Crude estimate of centre control (white - black)."""
    center = [chess.D4, chess.E4, chess.D5, chess.E5]
    score = 0
    for sq in center:
        piece = board.piece_at(sq)
        if piece and piece.color == chess.WHITE:
            score += 1
        if piece and piece.color == chess.BLACK:
            score -= 1
        if board.is_attacked_by(chess.WHITE, sq):
            score += 1
        if board.is_attacked_by(chess.BLACK, sq):
            score -= 1
    return score


def evaluate_king_safety(board: chess.Board) -> int:
    """Return a tiny king-safety differential (white - black)."""
    score = 0
    for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
        king_sq = board.king(color)
        if king_sq is None:
            continue
        attackers = len(board.attackers(not color, king_sq))
        defenders = len(board.attackers(color, king_sq))
        score += sign * (defenders - attackers)
    return score


def evaluate_pawn_structure(board: chess.Board) -> int:
    """Very small pawn-structure heuristic from White's perspective."""
    pawns: dict[bool, list[int]] = {chess.WHITE: [], chess.BLACK: []}
    for sq, piece in board.piece_map().items():
        if piece.piece_type == chess.PAWN:
            pawns[piece.color].append(sq)

    def is_passed(sq: int, color: bool, enemy_pawns: list[int]) -> bool:
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

    score = 0
    for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
        ours = pawns[color]
        files: dict[int, list[int]] = {}
        for sq in ours:
            files.setdefault(chess.square_file(sq), []).append(sq)

        isolated = 0
        doubled = 0
        passed = 0
        for file, sqs in files.items():
            if len(sqs) > 1:
                doubled += len(sqs) - 1
            for sq in sqs:
                if not files.get(file - 1) and not files.get(file + 1):
                    isolated += 1
                if is_passed(sq, color, pawns[not color]):
                    passed += 1

        score += sign * (passed - isolated - doubled)
    return score


def evaluate_pressure(board: chess.Board) -> int:
    """Return the pressure differential on valuable enemy pieces."""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }
    pressure = {chess.WHITE: 0, chess.BLACK: 0}
    for color in (chess.WHITE, chess.BLACK):
        for sq, piece in board.piece_map().items():
            if piece.color != color and board.is_attacked_by(color, sq):
                pressure[color] += piece_values[piece.piece_type]
    return pressure[chess.WHITE] - pressure[chess.BLACK]


def evaluate_synergy(board: chess.Board) -> int:
    """Return the difference in squares attacked by multiple pieces."""
    synergy = {chess.WHITE: 0, chess.BLACK: 0}
    for sq in chess.SQUARES:
        for color in (chess.WHITE, chess.BLACK):
            if len(board.attackers(color, sq)) >= 2:
                synergy[color] += 1
    return synergy[chess.WHITE] - synergy[chess.BLACK]


def evaluate_survivability(board: chess.Board) -> dict[bool, int]:
    """Return the capture risk for each side.

    A piece contributes to its colour's risk score when it is attacked by
    the opposing side and lacks any defenders of its own colour.  The score
    sums the standard piece values of all such vulnerable pieces.  Kings are
    ignored because they cannot be captured.
    """

    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,
    }
    risk = {chess.WHITE: 0, chess.BLACK: 0}
    for square, piece in board.piece_map().items():
        color = piece.color
        if board.is_attacked_by(not color, square) and not board.is_attacked_by(color, square):
            risk[color] += piece_values[piece.piece_type]
    return risk


__all__ = [
    "count_attacked_squares",
    "count_defended_pieces",
    "evaluate_center_control",
    "evaluate_king_safety",
    "evaluate_pawn_structure",
    "evaluate_pressure",
    "evaluate_synergy",
    "evaluate_survivability",
]
