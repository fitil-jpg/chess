"""Command-line entry point for :mod:`chess_ai`.

Imports vendored dependencies before executing a simple demonstration so
running ``python -m chess_ai`` uses the bundled third-party libraries.
"""

from vendors import setup_path  # noqa: F401

import chess

from utils import GameContext
from .random_bot import RandomBot


def main() -> None:
    """Play one random move from the initial position."""
    board = chess.Board()
    move, _ = RandomBot(chess.WHITE).choose_move(board, GameContext())
    print(move)


if __name__ == "__main__":
    main()
