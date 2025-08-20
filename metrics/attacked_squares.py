import chess


def calculate_attacked_squares(square: int, board: chess.Board) -> list[int]:
    """Calculate squares attacked from ``square`` on ``board``.

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
