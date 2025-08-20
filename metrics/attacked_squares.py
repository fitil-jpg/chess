import chess


def calculate_attacked_squares(square: int, board: chess.Board) -> list[int]:
    """Calculate squares attacked from ``square`` on ``board``.

    The function is a light wrapper around :meth:`chess.Board.attacks`.
    ``Board.attacks`` returns a :class:`chess.SquareSet`, which is converted
    into a regular ``list`` of integers to keep downstream assertions and
    metrics straightforward.

    Parameters
    ----------
    square:
        The board coordinate whose attacks are being calculated.
    board:
        The current :class:`chess.Board` instance.

    Returns
    -------
    list[int]
        Squares (as integers) that the piece on ``square`` attacks.

    Raises
    ------
    ValueError
        If ``square`` does not contain a piece on ``board``.
    """

    if board.piece_at(square) is None:
        raise ValueError(f"no piece at square {square}")

    attacked_squares: chess.SquareSet = board.attacks(square)
    return list(attacked_squares)
