#!/usr/bin/env python3
"""Generate self-play training data as lines of "FEN,outcome".

Each visited position is recorded with the final game outcome from the
perspective of the side to move in that position: 1 for a win, -1 for a loss,
0 for a draw. Output is written to a text file suitable for
``chess_ai.nn.train.FenOutcomeDataset``.

Example:
  python scripts/generate_selfplay_data.py --games 50 --white NeuralBot --black NeuralBot --out data/selfplay_fens.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import chess

import sys
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chess_ai.bot_agent import make_agent, get_agent_names  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate self-play FEN,outcome data")
    p.add_argument("--games", type=int, default=20, help="Number of games to play")
    p.add_argument("--white", default="NeuralBot", help="White agent name")
    p.add_argument("--black", default="NeuralBot", help="Black agent name")
    p.add_argument("--out", default="selfplay_data.txt", help="Output file path")
    p.add_argument("--max-plies", type=int, default=400, dest="max_plies", help="Safeguard max plies per game")
    return p.parse_args()


def _play_game_collect(white, black, max_plies: int) -> Tuple[str, List[str]]:
    board = chess.Board()
    fens_by_turn: List[str] = []
    while not board.is_game_over() and len(board.move_stack) < max_plies:
        fens_by_turn.append(board.fen())
        agent = white if board.turn == chess.WHITE else black
        try:
            ret = agent.choose_move(board)
        except TypeError:
            ret = agent.choose_move(board, debug=True)
        move = ret[0] if isinstance(ret, tuple) else ret
        if move is None or not board.is_legal(move):
            break
        board.push(move)
    try:
        result = board.result(claim_draw=True)
    except TypeError:
        result = board.result()
    return result, fens_by_turn


def _result_to_score(result: str, side_to_move_was_white: bool) -> int:
    if result == "1-0":
        return 1 if side_to_move_was_white else -1
    if result == "0-1":
        return -1 if side_to_move_was_white else 1
    return 0


def main() -> int:
    args = _parse_args()

    available = set(get_agent_names())
    if args.white not in available or args.black not in available:
        print(f"Unknown agent(s). Available: {sorted(available)}")
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as fh:
        for i in range(args.games):
            white = make_agent(args.white, chess.WHITE)
            black = make_agent(args.black, chess.BLACK)
            result, fens = _play_game_collect(white, black, args.max_plies)
            for fen in fens:
                # FEN indicates side to move in the field after the board
                side_to_move_w = (fen.split()[1] == 'w')
                outcome = _result_to_score(result, side_to_move_w)
                fh.write(f"{fen},{outcome}\n")
            print(f"[{i+1}/{args.games}] {args.white} vs {args.black}: {result} | positions={len(fens)}")

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

