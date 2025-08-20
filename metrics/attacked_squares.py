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
        Board coordinate of the piece represented as an ``int`` in ``[0, 63]``.
    board:
        The current :class:`chess.Board` instance.

    Returns
    -------
    list[int]
        Squares (as integers) that the piece attacks.
    """

    return list(board.attacks(square))
