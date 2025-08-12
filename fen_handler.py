
from typing import List, Optional

fen_mapping = {
    'p': 'black-pawn',
    'r': 'black-rook',
    'n': 'black-knight',
    'b': 'black-bishop',
    'q': 'black-queen',
    'k': 'black-king',
    'P': 'white-pawn',
    'R': 'white-rook',
    'N': 'white-knight',
    'B': 'white-bishop',
    'Q': 'white-queen',
    'K': 'white-king'
}

def fen_to_board_state(fen: str) -> List[List[Optional[str]]]:
    """Convert a FEN string into a board representation.

    Parameters
    ----------
    fen: str
        Forsyth-Edwards Notation string describing the board position.

    Returns
    -------
    List[List[Optional[str]]]
        Nested list representing rows of the board where each element is a
        piece name from ``fen_mapping`` or ``None`` for an empty square.
    """

    board_state = []
    rows = fen.split()[0].split('/')
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                board_row.extend([None] * int(char))
            else:
                board_row.append(fen_mapping.get(char, None))
        board_state.append(board_row)
    return board_state

def load_fens_from_file(path: str) -> List[List[List[Optional[str]]]]:
    """Read multiple FEN strings from a file.

    Parameters
    ----------
    path: str
        Path to a text file containing one FEN string per line.

    Returns
    -------
    List[List[List[Optional[str]]]]
        List of board states, each in the format returned by
        :func:`fen_to_board_state`.
    """

    positions = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                positions.append(fen_to_board_state(line))
    return positions
