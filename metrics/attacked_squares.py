import chess


def calculate_attacked_squares(piece: chess.Piece, board: chess.Board) -> list[int]:
    """Calculate squares ``piece`` attacks on ``board``.

    The function is a light wrapper around :meth:`chess.Board.attacks`.
    ``Board.attacks`` returns a :class:`chess.SquareSet`, which is converted
    into a regular ``list`` of integers to keep downstream assertions and
    metrics straightforward.

    Parameters
    ----------
    piece:
        The :class:`chess.Piece` whose attacks are being calculated.  The
        function verifies that this piece exists on ``board``.
    board:
        The current :class:`chess.Board` instance.

    Returns
    -------
    list[int]
        Squares (as integers) that ``piece`` attacks.

    Raises
    ------
    ValueError
        If ``piece`` is not present on ``board``.
    """

    piece_squares = board.pieces(piece.piece_type, piece.color)
    if not piece_squares:
        raise ValueError("Piece is not on the board")

    piece_square = piece_squares.pop()
    attacked_squares = board.attacks(piece_square)
    return list(attacked_squares)
