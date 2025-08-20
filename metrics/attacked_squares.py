import chess


def calculate_attacked_squares(square: chess.Square, board: chess.Board) -> list[int]:
    """Calculate squares a piece on ``square`` attacks on ``board``.

    The function is a light wrapper around :meth:`chess.Board.attacks`.
    ``Board.attacks`` returns a :class:`chess.SquareSet`, which is converted
    into a regular ``list`` of integers to keep downstream assertions and
    metrics straightforward.

    Parameters
    ----------
    square:
        The board coordinate containing the piece whose attacks are being
        calculated.
    board:
        The current :class:`chess.Board` instance.

    Returns
    -------
    list[int]
        Squares (as integers) that the piece on ``square`` attacks.

    Raises
    ------
    ValueError
        If ``square`` does not contain a piece.
    """

    if board.piece_at(square) is None:
        raise ValueError("Piece is not on the board")

    attacked_squares = board.attacks(square)
    return list(attacked_squares)
