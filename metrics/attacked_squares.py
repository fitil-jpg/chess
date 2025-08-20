import chess


def calculate_attacked_squares(board: chess.Board, square: chess.Square) -> list[int]:
    """Return all squares attacked by the piece on ``square``.

    ``python-chess`` provides :func:`Board.attacks` which yields the set of
    target squares for the piece currently occupying ``square``.  The helper
    simply converts that iterable into a list so tests can easily assert on the
    result.
    """

    return list(board.attacks(square))
