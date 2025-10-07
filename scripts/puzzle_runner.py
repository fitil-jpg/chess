#!/usr/bin/env python3
"""Run themed puzzle suites and score agent performance.

Puzzle format: JSON Lines (one JSON object per line).
Each object:
  {"id": "mate1_001", "fen": "<FEN>", "judge": "mate_in_1"}
Supported judges:
  - mate_in_1: success if the chosen move delivers immediate checkmate
  - gives_check: success if move gives check
  - capture_hanging: success if move is a capture of a piece with 0 defenders before the move

Examples:
  python scripts/puzzle_runner.py --agent DynamicBot --suite puzzles/themes/mate_in_1.jsonl --limit 50 --runs output
  python scripts/puzzle_runner.py --agent AggressiveBot --suite puzzles/themes --runs output
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import chess

# Ensure project root is on sys.path when running via absolute script path
import sys
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chess_ai.bot_agent import make_agent, get_agent_names  # noqa: E402


@dataclass
class Puzzle:
    pid: str
    fen: str
    judge: str


def _iter_puzzles(path: Path) -> Iterable[Puzzle]:
    if path.is_dir():
        for f in sorted(path.glob("*.jsonl")):
            yield from _iter_puzzles(f)
        return
    with path.open("r", encoding="utf-8") as fh:
        for ln, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                yield Puzzle(obj.get("id", f"{path.name}:{ln}"), obj["fen"], obj["judge"])  # type: ignore
            except Exception as e:
                raise SystemExit(f"Malformed JSONL at {path}:{ln}: {e}")


def _play_one(board: chess.Board, agent) -> chess.Move | None:
    try:
        ret = agent.choose_move(board)
    except TypeError:
        ret = agent.choose_move(board, debug=True)
    return ret[0] if isinstance(ret, tuple) else ret


# ------------------------- Judges --------------------------------------------

def judge_mate_in_1(board: chess.Board, move: chess.Move) -> bool:
    tmp = board.copy(stack=False)
    tmp.push(move)
    return tmp.is_checkmate()


def judge_gives_check(board: chess.Board, move: chess.Move) -> bool:
    tmp = board.copy(stack=False)
    tmp.push(move)
    return tmp.is_check()


def judge_capture_hanging(board: chess.Board, move: chess.Move) -> bool:
    if not board.is_capture(move):
        return False
    enemy = not board.turn
    defenders = board.attackers(enemy, move.to_square)
    return len(defenders) == 0


JUDGES: Dict[str, Callable[[chess.Board, chess.Move], bool]] = {
    "mate_in_1": judge_mate_in_1,
    "gives_check": judge_gives_check,
    "capture_hanging": judge_capture_hanging,
}


# ----------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run themed puzzle suites")
    p.add_argument("--agent", default="DynamicBot", help="Agent name to test")
    p.add_argument("--suite", required=True, help="Path to JSONL file or directory of suites")
    p.add_argument("--limit", type=int, default=0, help="Max puzzles to run (0=all)")
    p.add_argument("--runs", default="output", help="Directory to save JSON results")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    names = set(get_agent_names())
    if args.agent not in names:
        print(f"Unknown agent '{args.agent}'. Available: {sorted(names)}")
        return 2

    agent = None  # type: ignore
    total = 0
    ok = 0
    per_theme: Dict[str, Dict[str, int]] = {}
    details: List[Dict[str, object]] = []

    suite_path = Path(args.suite)

    for pz in _iter_puzzles(suite_path):
        if args.limit and total >= args.limit:
            break
        board = chess.Board(pz.fen)
        agent = make_agent(args.agent, board.turn)
        move = _play_one(board, agent)
        if move is None or not board.is_legal(move):
            success = False
        else:
            judge = JUDGES.get(pz.judge)
            if judge is None:
                print(f"Unknown judge '{pz.judge}' for puzzle {pz.pid}; counting as failure")
                success = False
            else:
                success = judge(board, move)
        total += 1
        ok += int(success)
        rec = per_theme.setdefault(pz.judge, {"total": 0, "ok": 0})
        rec["total"] += 1
        rec["ok"] += int(success)
        details.append({
            "id": pz.pid,
            "fen": pz.fen,
            "judge": pz.judge,
            "move": (move.uci() if move else None),
            "success": success,
        })

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(args.runs).mkdir(parents=True, exist_ok=True)
    out_path = Path(args.runs) / f"puzzles_{args.agent}_{ts}.json"
    payload = {
        "schema_version": 1,
        "task": "puzzle_suite",
        "timestamp": ts,
        "agent": args.agent,
        "suite": str(suite_path),
        "total": total,
        "solved": ok,
        "accuracy": (ok / total) if total else 0.0,
        "per_theme": {k: {"total": v["total"], "ok": v["ok"], "accuracy": (v["ok"] / v["total"]) if v["total"] else 0.0} for k, v in per_theme.items()},
        "details": details,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}  |  accuracy={(payload['accuracy']*100):.1f}%  total={total}")
    for theme, rec in payload["per_theme"].items():
        print(f"  {theme}: {(rec['accuracy']*100):.1f}% ({rec['ok']}/{rec['total']})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
