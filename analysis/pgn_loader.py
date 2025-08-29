"""Utilities for streaming games from PGN files.

This module provides :func:`stream_pgn_games` which reads games one by one
from a PGN file without loading the entire file into memory. For every game
it yields a dictionary containing the list of FEN strings before each move,
the corresponding moves in UCI format and the PGN headers as metadata.

Basic filtering is supported via optional parameters:

``move``
    Only include positions that occur in the specified *full move* number.

``player``
    Restrict to positions where it is either ``chess.WHITE`` or
    ``chess.BLACK`` to move.

``phase``
    Keep only positions that fall into the requested phase. The phase is
    determined by a simple heuristic based on the number of pieces on the
    board:

    - more than 20 pieces  -> "opening"
    - more than 10 pieces  -> "middlegame"
    - 10 pieces or fewer   -> "endgame"

The function yields games that have at least one position after filtering.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator, List, Optional

import chess
import chess.pgn


def _classify_phase(board: chess.Board) -> str:
    """Return a coarse phase classification for *board*.

    The classification uses only the remaining material on the board which is
    sufficient for simple filtering tasks.
    """

    piece_count = len(board.piece_map())
    if piece_count > 20:
        return "opening"
    if piece_count > 10:
        return "middlegame"
    return "endgame"


def stream_pgn_games(
    path: str,
    *,
    move: Optional[int] = None,
    player: Optional[chess.Color] = None,
    phase: Optional[str] = None,
) -> Iterator[Dict[str, object]]:
    """Yield games from *path* one by one.

    Parameters
    ----------
    path:
        Path to a PGN file.
    move:
        Optional full-move number to filter positions.
    player:
        When provided, keep only positions where ``board.turn`` equals this
        value (``chess.WHITE`` or ``chess.BLACK``).
    phase:
        Restrict positions to those whose board state is classified as the
        given phase.

    Yields
    ------
    Dict[str, object]
        A dictionary with ``"fens"``, ``"moves"`` and ``"metadata"`` keys for
        each game.
    """

    pgn_path = Path(path)
    with pgn_path.open("r", encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break

            board = game.board()
            fens: List[str] = []
            moves: List[str] = []

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

                fens.append(board.fen())
                moves.append(mv.uci())
                board.push(mv)

            if fens:
                yield {"fens": fens, "moves": moves, "metadata": dict(game.headers)}
