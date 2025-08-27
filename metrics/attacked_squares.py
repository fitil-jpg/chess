import chess
from typing import List

def calculate_attacked_squares(board: chess.Board, square: int) -> List[int]:
    """Calculate squares a piece on ``square`` attacks on ``board``.

    The function is a light wrapper around :meth:`chess.Board.attacks`.
    ``Board.attacks`` returns a :class:`chess.SquareSet`, which is converted
    into a regular ``list`` of integers to keep downstream assertions and
    metrics straightforward.

    Parameters
    ----------
    board:
        The current :class:`chess.Board` instance.
    square:
        The integer index of the square from which to calculate attacks.

    Returns
    -------
    List[int]
        Squares (as integers) that the piece on ``square`` attacks.

    Raises
    ------
    ValueError
        If there is no piece on ``square``.
    """

    piece = board.piece_at(square)
    if piece is None:
        raise ValueError(f"no piece at square {square}")

    attacked_squares: chess.SquareSet = board.attacks(square)
    return list(attacked_squares)
