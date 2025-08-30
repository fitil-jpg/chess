from __future__ import annotations

"""Convert PGN games into FEN positions.

This script reads one or more games from a PGN file and prints the FEN string
before each move.  Optional filters allow restricting the output to a specific
full move number, side to move, or game phase.

Example
-------
Extract all opening positions where White is to move::

    python analysis/pgn_to_fen.py games.pgn --player white --phase opening

"""

import argparse
from pathlib import Path
from typing import Iterator, Optional

import chess
import chess.pgn


def _classify_phase(board: chess.Board) -> str:
    """Return a coarse phase classification for *board*.

    The classification is based on remaining pieces only, which suffices for
    simple filtering tasks.  Positions with more than 20 pieces are considered
    the opening, those with more than 10 pieces the middlegame and everything
    else the endgame.
    """

    piece_count = len(board.piece_map())
    if piece_count > 20:
        return "opening"
    if piece_count > 10:
        return "middlegame"
    return "endgame"


def iter_fens(
    path: str,
    *,
    move: Optional[int] = None,
    player: Optional[chess.Color] = None,
    phase: Optional[str] = None,
) -> Iterator[str]:
    """Yield FEN strings from *path* that satisfy the given filters."""

    pgn_path = Path(path)
    with pgn_path.open("r", encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break

            board = game.board()
            for mv in game.mainline_moves():
                if move is not None and board.fullmove_number != move:
                    board.push(mv)
                    continue
                if player is not None and board.turn != player:
                    board.push(mv)
                    continue
                if phase is not None and _classify_phase(board) != phase:
                    board.push(mv)
                    continue

                yield board.fen()
                board.push(mv)


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit FEN strings from a PGN file")
    parser.add_argument("pgn", help="Path to the PGN file")
    parser.add_argument(
        "--player",
        choices=["white", "black"],
        help="Keep only positions where the specified side is to move",
    )
    parser.add_argument(
        "--move",
        type=int,
        help="Only include positions that occur in this full move number",
    )
    parser.add_argument(
        "--phase",
        choices=["opening", "middlegame"],
        help="Restrict positions to the given game phase",
    )
    args = parser.parse_args()

    player: Optional[chess.Color]
    if args.player == "white":
        player = chess.WHITE
    elif args.player == "black":
        player = chess.BLACK
    else:
        player = None

    for fen in iter_fens(args.pgn, move=args.move, player=player, phase=args.phase):
        print(fen)


if __name__ == "__main__":
    main()
