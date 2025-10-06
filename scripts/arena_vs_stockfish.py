#!/usr/bin/env python3
"""Run games between our bot and Stockfish and record runs.

Usage:
  python scripts/arena_vs_stockfish.py --games 10 --white DynamicBot --black StockfishBot \
      --sf-path /usr/bin/stockfish --sf-elo 2200 --think-ms 200 --runs runs
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, List

import chess

# Ensure project root is on sys.path when running via absolute script path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chess_ai.bot_agent import make_agent, get_agent_names


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Play games vs Stockfish and log runs")
    p.add_argument("--games", type=int, default=4)
    p.add_argument("--white", default="DynamicBot", help="White agent name")
    p.add_argument("--black", default="StockfishBot", help="Black agent name")
    p.add_argument("--sf-path", dest="sf_path", help="Path to stockfish binary")
    p.add_argument("--sf-elo", dest="sf_elo", type=int)
    p.add_argument("--sf-skill", dest="sf_skill", type=int)
    p.add_argument("--think-ms", dest="think_ms", type=int, default=200)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--hash-mb", dest="hash_mb", type=int, default=128)
    p.add_argument("--runs", default="runs", help="Output directory for run JSONs")
    return p.parse_args()


def _make(name: str, color: bool, args: argparse.Namespace):
    # StockfishBot supports config via env variables and kwargs
    if name == "StockfishBot":
        if args.sf_path:
            os.environ.setdefault("STOCKFISH_PATH", args.sf_path)
        # Instantiate directly to pass params
        from chess_ai.stockfish_bot import StockfishBot
        return StockfishBot(
            color,
            path=args.sf_path,
            think_time_ms=args.think_ms,
            skill_level=args.sf_skill,
            uci_elo=args.sf_elo,
            threads=args.threads,
            hash_mb=args.hash_mb,
        )
    return make_agent(name, color)


def play_game(white, black) -> Tuple[chess.Board, List[str], List[str], List[str]]:
    board = chess.Board()
    moves_log: List[str] = []
    fens_log: List[str] = []
    modules_w: List[str] = []
    modules_b: List[str] = []

    while not board.is_game_over():
        color = board.turn
        agent = white if color == chess.WHITE else black
        # Try to get (move, reason), else assume simple move
        try:
            ret = agent.choose_move(board)
        except TypeError:
            ret = agent.choose_move(board, debug=True)

        if isinstance(ret, tuple):
            move, reason = ret[0], ("" if len(ret) < 2 else str(ret[1]))
        else:
            move, reason = ret, ""

        if move is None or not board.is_legal(move):
            break
        san_before = board.san(move)
        board.push(move)

        moves_log.append(san_before)
        fens_log.append(board.fen())
        if color == chess.WHITE:
            modules_w.append(reason)
        else:
            modules_b.append(reason)

    return board, moves_log, fens_log, modules_w, modules_b


def main() -> int:
    args = _parse_args()
    names = set(get_agent_names()) | {"StockfishBot"}
    if args.white not in names or args.black not in names:
        print(f"Unknown agent(s). Available: {sorted(names)}")
        return 2

    Path(args.runs).mkdir(parents=True, exist_ok=True)

    for i in range(args.games):
        white = _make(args.white, chess.WHITE, args)
        black = _make(args.black, chess.BLACK, args)
        board, moves, fens, modules_w, modules_b = play_game(white, black)
        res = board.result()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_path = Path(args.runs) / f"{ts}.json"
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(
                {
                    "moves": moves,
                    "fens": fens,
                    "modules_w": modules_w,
                    "modules_b": modules_b,
                    "result": res,
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )
        try:
            # Cleanly close engine if applicable
            if hasattr(white, "close"):
                white.close()
            if hasattr(black, "close"):
                black.close()
        except Exception:
            pass
        print(f"Game {i+1}/{args.games} finished: {res} -> {out_path}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI utility
    raise SystemExit(main())
