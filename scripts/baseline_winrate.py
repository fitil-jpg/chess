#!/usr/bin/env python3
"""Evaluate win-rate of a subject agent vs baseline agents.

Examples:
  python scripts/baseline_winrate.py --agent DynamicBot --baselines RandomBot,AggressiveBot,FortifyBot --games 20 --runs output

This script alternates colors and reports per-baseline and overall win-rate.
Outputs JSON to the --runs directory.
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
    p = argparse.ArgumentParser(description="Baseline win-rate evaluation")
    p.add_argument("--agent", default="DynamicBot", help="Subject agent name")
    p.add_argument("--baselines", default="RandomBot,AggressiveBot,FortifyBot",
                   help="Comma-separated baseline agent names")
    p.add_argument("--games", type=int, default=20, help="Games per baseline (total across both colors)")
    p.add_argument("--runs", default="output", help="Directory to save JSON results")
    return p.parse_args()


def _play_game(white, black) -> str:
    board = chess.Board()
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
        board.push(move)
    try:
        return board.result(claim_draw=True)
    except TypeError:
        return board.result()


def main() -> int:
    args = _parse_args()

    names = set(get_agent_names())
    if args.agent not in names:
        print(f"Unknown subject agent '{args.agent}'. Available: {sorted(names)}")
        return 2

    baselines = [b.strip() for b in args.baselines.split(",") if b.strip()]
    unknown = [b for b in baselines if b not in names]
    if unknown:
        print(f"Unknown baselines: {unknown}. Available: {sorted(names)}")
        return 2

    per_baseline: Dict[str, Dict[str, int]] = {}
    total_w = total_l = total_d = 0

    for b in baselines:
        w = l = d = 0
        games_for_white = args.games // 2
        games_for_black = args.games - games_for_white

        # Subject as white
        for _ in range(games_for_white):
            white = make_agent(args.agent, chess.WHITE)
            black = make_agent(b, chess.BLACK)
            res = _play_game(white, black)
            if res == "1-0":
                w += 1
            elif res == "0-1":
                l += 1
            else:
                d += 1

        # Subject as black
        for _ in range(games_for_black):
            white = make_agent(b, chess.WHITE)
            black = make_agent(args.agent, chess.BLACK)
            res = _play_game(white, black)
            if res == "1-0":
                l += 1
            elif res == "0-1":
                w += 1
            else:
                d += 1

        per_baseline[b] = {"wins": w, "losses": l, "draws": d, "win_rate": (w + 0.5*d) / max(1, (w+l+d))}
        total_w += w; total_l += l; total_d += d

    overall_wr = (total_w + 0.5*total_d) / max(1, (total_w + total_l + total_d))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(args.runs).mkdir(parents=True, exist_ok=True)
    out_path = Path(args.runs) / f"winrate_{args.agent}_{ts}.json"
    payload = {
        "schema_version": 1,
        "task": "baseline_winrate",
        "timestamp": ts,
        "subject": args.agent,
        "baselines": baselines,
        "per_baseline": per_baseline,
        "overall": {"wins": total_w, "losses": total_l, "draws": total_d, "win_rate": overall_wr},
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    for b in baselines:
        rec = per_baseline[b]
        print(f"{args.agent} vs {b}: W {rec['wins']}  L {rec['losses']}  D {rec['draws']}  WR={(rec['win_rate']*100):.1f}%")
    print(f"OVERALL WR: {(overall_wr*100):.1f}%  (W{total_w}/L{total_l}/D{total_d})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
