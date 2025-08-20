import chess


def calculate_attacked_squares(piece: chess.Piece, board: chess.Board) -> list[int]:
    """Calculate squares attacked by ``piece`` on ``board``.

    Parameters
    ----------
    piece:
        :class:`chess.Piece` instance whose attacks to compute. The piece must be
        present on ``board``.
    board:
        The current :class:`chess.Board` instance.

    Returns
    -------
    list[int]
        Squares (as integers) that the piece attacks.

    Raises
    ------
    ValueError
        If ``piece`` is not present on ``board``.
    """

    squares = board.pieces(piece.piece_type, piece.color)
    if not squares:
        raise ValueError("piece is not on the board")

    piece_square = squares.pop()
    attacked_squares = board.attacks(piece_square)
    return list(attacked_squares)
