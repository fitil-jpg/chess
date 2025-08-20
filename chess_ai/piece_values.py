import chess

# Base piece values in centipawns
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

CENTER_SQUARES = [chess.E4, chess.D4, chess.E5, chess.D5]


def dynamic_piece_value(piece: chess.Piece, board: chess.Board) -> int:
    """Return a context aware value for ``piece`` on ``board``.

    The base material value is adjusted by:
      * mobility (number of squares the piece attacks)
      * control of central squares
      * opponent material (pieces become slightly more valuable as the
        opponent loses major material such as the queen)
    """
    base = PIECE_VALUES[piece.piece_type]

    # Locate the piece's square
    square = next((sq for sq, p in board.piece_map().items() if p == piece), None)
    if square is None:
        return base

    attacks = board.attacks(square)
    mobility_bonus = len(attacks)
    center_bonus = sum(10 for sq in attacks if sq in CENTER_SQUARES)

    enemy_color = not piece.color
    enemy_material = sum(
        PIECE_VALUES[p.piece_type] for p in board.piece_map().values() if p.color == enemy_color
    )
    # Boost value if the opponent has lost their queen
    material_factor = 1.1 if not board.pieces(chess.QUEEN, enemy_color) else 1.0
    material_factor += (3900 - enemy_material) / 3900 * 0.05

    return int((base + mobility_bonus + center_bonus) * material_factor)
