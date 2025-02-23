import chess

def calculate_attacked_squares(piece: chess.Piece, board: chess.Board):
    """
    Calculate all squares attacked by a given piece on the board.
    :param piece: A chess.Piece instance
    :param board: A chess.Board instance
    :return: A list of squares (as integers) that the piece attacks
    """
    piece_square = next(
        square for square in chess.SQUARES
        if board.piece_at(square) == piece
    )
    attacked_squares = board.attacks(piece_square)
    return list(attacked_squares)