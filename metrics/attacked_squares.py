import chess


def calculate_attacked_squares(square: chess.Square, board: chess.Board) -> list[int]:
    """Calculate squares attacked from ``square`` on ``board``.

    Parameters
    ----------
    square:
        :class:`chess.Square` where the piece resides.
    board:
        The current :class:`chess.Board` instance.

    Returns
    -------
    list[int]
        Squares (as integers) that the piece attacks.
    """
    return list(board.attacks(square))
