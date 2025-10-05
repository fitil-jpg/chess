import chess
from typing import Dict, Iterable, List, Optional, Set, Tuple


def calculate_defended_squares(board: chess.Board, square: int) -> List[int]:
    """Return squares defended by the piece on ``square``.

    A defended square is any square that the piece on ``square`` attacks and
    that is currently occupied by a piece of the same colour.
    """
    piece = board.piece_at(square)
    if piece is None:
        raise ValueError(f"no piece at square {square}")

    defended: List[int] = []
    for target in board.attacks(square):
        occupant = board.piece_at(target)
        if occupant is None:
            continue
        if occupant.color == piece.color:
            defended.append(target)
    return defended


def build_defense_map(
    board: chess.Board,
    *,
    attack_map: Optional[Dict[int, Iterable[int]]] = None,
) -> Dict[str, Set[int]]:
    """Return mapping of colour name to defended squares on the board.

    Parameters
    ----------
    board:
        The current board.
    attack_map:
        Optional precomputed mapping of ``from_square -> attacked_squares``.
        If provided, it is used instead of calling :meth:`chess.Board.attacks`
        for each piece, which may be beneficial if an attack map is already
        available from a previous computation.
    """
    defense_map: Dict[str, Set[int]] = {"white": set(), "black": set()}

    # Build a quick lookup for piece colours by square
    piece_color_by_square: Dict[int, bool] = {
        sq: piece.color for sq, piece in board.piece_map().items()
    }

    for sq, piece in board.piece_map().items():
        color_key = "white" if piece.color == chess.WHITE else "black"
        attacks: Iterable[int]
        if attack_map is not None and sq in attack_map:
            attacks = attack_map[sq]
        else:
            attacks = board.attacks(sq)

        for target in attacks:
            occupant_color = piece_color_by_square.get(target)
            if occupant_color is None:
                continue
            if occupant_color == piece.color:
                defense_map[color_key].add(target)

    return defense_map
