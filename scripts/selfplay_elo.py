#!/usr/bin/env python3
"""Round-robin self-play Elo rating between internal agents.

Examples:
  python scripts/selfplay_elo.py --agents DynamicBot,AggressiveBot,FortifyBot --rounds 10 --runs output

Notes:
- Ratings start at 1500 and update per game using Elo with K-factor.
- Each pairing plays ``rounds`` games for each color (2*rounds total per pair).
- Results are saved to JSON with a stable schema.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import chess

# Ensure project root is on sys.path when running via absolute script path
import sys
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chess_ai.bot_agent import make_agent, get_agent_names  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Round-robin self-play Elo rating between agents")
    p.add_argument("--agents", default="DynamicBot,FortifyBot, AggressiveBot",
                   help="Comma-separated list of agent names")
    p.add_argument("--rounds", type=int, default=8, help="Games per color per pairing")
    p.add_argument("--k-factor", type=float, default=24.0, dest="k")
    p.add_argument("--runs", default="output", help="Directory to save JSON results")
    p.add_argument("--seed", type=int, default=0, help="Reserved for future stochastic agents")
    return p.parse_args()


def _play_game(white, black) -> Tuple[str, List[str]]:
    """Play a single game and return (result_str, san_moves).

    result_str is one of: "1-0", "0-1", "1/2-1/2".
    """
    board = chess.Board()
    moves_log: List[str] = []

    while not board.is_game_over():
        color = board.turn
        agent = white if color == chess.WHITE else black
        try:
            ret = agent.choose_move(board)
        except TypeError:
            ret = agent.choose_move(board, debug=True)
        move = ret[0] if isinstance(ret, tuple) else ret
        if move is None or not board.is_legal(move):
            break
        san_before = board.san(move)
        board.push(move)
        moves_log.append(san_before)

    try:
        res = board.result(claim_draw=True)
    except TypeError:
        res = board.result()
    return res, moves_log


def _elo_expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))


def _elo_update(ra: float, rb: float, score_a: float, k: float) -> Tuple[float, float]:
    ea = _elo_expected(ra, rb)
    eb = _elo_expected(rb, ra)
    ra_new = ra + k * (score_a - ea)
    rb_new = rb + k * ((1.0 - score_a) - eb)
    return ra_new, rb_new


def main() -> int:
    args = _parse_args()

    available = set(get_agent_names())
    requested = [a.strip() for a in args.agents.split(",") if a.strip()]
    unknown = [a for a in requested if a not in available]
    if unknown:
        print(f"Unknown agents: {unknown}. Available: {sorted(available)}")
        return 2

    ratings: Dict[str, float] = {a: 1500.0 for a in requested}
    games: List[Dict[str, object]] = []

    # All pairings (i < j)
    for i in range(len(requested)):
        for j in range(i + 1, len(requested)):
            a, b = requested[i], requested[j]
            for r in range(args.rounds):
                # A as white
                white = make_agent(a, chess.WHITE)
                black = make_agent(b, chess.BLACK)
                result, moves = _play_game(white, black)
                if result == "1-0":
                    ratings[a], ratings[b] = _elo_update(ratings[a], ratings[b], 1.0, args.k)
                elif result == "0-1":
                    ratings[a], ratings[b] = _elo_update(ratings[a], ratings[b], 0.0, args.k)
                else:
                    ratings[a], ratings[b] = _elo_update(ratings[a], ratings[b], 0.5, args.k)
                games.append({"white": a, "black": b, "result": result, "round": r, "color": "Awhite"})

                # B as white
                white = make_agent(b, chess.WHITE)
                black = make_agent(a, chess.BLACK)
                result, moves = _play_game(white, black)
                if result == "1-0":
                    ratings[b], ratings[a] = _elo_update(ratings[b], ratings[a], 1.0, args.k)
                elif result == "0-1":
                    ratings[b], ratings[a] = _elo_update(ratings[b], ratings[a], 0.0, args.k)
                else:
                    ratings[b], ratings[a] = _elo_update(ratings[b], ratings[a], 0.5, args.k)
                games.append({"white": b, "black": a, "result": result, "round": r, "color": "Bwhite"})

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(args.runs).mkdir(parents=True, exist_ok=True)
    out_path = Path(args.runs) / f"selfplay_elo_{ts}.json"
    payload = {
        "schema_version": 1,
        "task": "selfplay_elo",
        "timestamp": ts,
        "agents": requested,
        "k_factor": args.k,
        "ratings": ratings,
        "games": games,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    for a in sorted(ratings, key=ratings.get, reverse=True):
        print(f"{a:>14}: {ratings[a]:7.1f}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
