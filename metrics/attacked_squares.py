import chess
from typing import Union


def calculate_attacked_squares(square: Union[int, chess.Square], board: chess.Board) -> list[int]:
    """Calculate squares attacked from ``square`` on ``board``.

    Parameters
    ----------
    square:
        Index or :class:`chess.Square` where the piece resides.
    board:
        The current :class:`chess.Board` instance.

    Returns
    -------
    list[int]
        Squares (as integers) that the piece attacks.
    """
    square_index = int(square)
    return list(board.attacks(square_index))
