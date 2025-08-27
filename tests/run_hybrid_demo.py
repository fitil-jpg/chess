"""HybridBot demonstration script.

Runs a few plies from the initial position with :class:`HybridBot` and prints
basic diagnostics for each move.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chess

if not hasattr(chess.Board, "transposition_key"):
    chess.Board.transposition_key = chess.Board._transposition_key  # type: ignore[attr-defined]

from chess_ai.bot_agent import HybridBot


def main() -> None:
    """Run a few plies with ``HybridBot`` from the initial position."""
    board = chess.Board()
    bots = {
        chess.WHITE: HybridBot(chess.WHITE),
        chess.BLACK: HybridBot(chess.BLACK),
    }

    for ply in range(4):
        bot = bots[board.turn]
        start = time.perf_counter()
        move, diag = bot.impl.choose_move(board)  # type: ignore[union-attr]
        elapsed = time.perf_counter() - start
        board.push(move)

        chosen = diag.get("chosen")
        cand = next(
            (c for c in diag.get("candidates", []) if c["move"] == chosen),
            {},
        )
        mcts = cand.get("mcts", 0.0)
        ab = cand.get("ab", 0.0)
        print(
            f"{ply + 1}. {move.uci()} | MCTS={mcts:.3f} AB={ab:.3f} time={elapsed:.2f}s"
        )

    print(board)


if __name__ == "__main__":
    main()
