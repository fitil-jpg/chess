#!/usr/bin/env python3
"""Unified benchmark harness for chess agents.

Provides three workflows and optional baseline delta computation:
- ladder: Round-robin self-play Elo among agents
- suites: Fixed FEN suites (tactics/endgames) with judges
- ab:     A/B head-to-head mini-arenas

Examples:
  # Run all with small counts
  python scripts/bench.py \
    --tasks ladder,suites,ab \
    --agents DynamicBot,AggressiveBot,FortifyBot \
    --rounds 2 --games 8 --limit 20 \
    --suites puzzles/themes/mate_in_1.jsonl,puzzles/endgames/minimal.jsonl \
    --runs output

  # Compute deltas against a previous run
  python scripts/bench.py --baseline output/bench_20250101_120000.json

Notes:
- Ratings start at 1500 with a configurable K-factor.
- All outputs are written to a single JSON artifact under --runs.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import chess

# Ensure project root on sys.path when running via absolute path
import sys
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chess_ai.bot_agent import make_agent, get_agent_names  # noqa: E402


# ---------------------------- Utilities ---------------------------------------

def _safe_choose_move(agent, board: chess.Board):
    try:
        ret = agent.choose_move(board)
    except TypeError:
        ret = agent.choose_move(board, debug=True)
    # Many agents return (move, reason). Some return just move.
    return ret[0] if isinstance(ret, tuple) else ret


def _play_game(white, black) -> Tuple[str, List[str]]:
    """Play a single game and return (result_str, san_moves)."""
    board = chess.Board()
    moves_log: List[str] = []
    while not board.is_game_over():
        agent = white if board.turn == chess.WHITE else black
        move = _safe_choose_move(agent, board)
        if move is None or not board.is_legal(move):
            break
        san = board.san(move)
        board.push(move)
        moves_log.append(san)
    try:
        result = board.result(claim_draw=True)
    except TypeError:
        result = board.result()
    return result, moves_log


def _elo_expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))


def _elo_update(ra: float, rb: float, score_a: float, k: float) -> Tuple[float, float]:
    ea = _elo_expected(ra, rb)
    eb = _elo_expected(rb, ra)
    ra_new = ra + k * (score_a - ea)
    rb_new = rb + k * ((1.0 - score_a) - eb)
    return ra_new, rb_new


# ---------------------------- Suites ------------------------------------------
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
            obj = json.loads(line)
            yield Puzzle(obj.get("id", f"{path.name}:{ln}"), obj["fen"], obj["judge"])  # type: ignore


def judge_mate_in_1(board: chess.Board, move: chess.Move) -> bool:
    t = board.copy(stack=False); t.push(move)
    return t.is_checkmate()


def judge_gives_check(board: chess.Board, move: chess.Move) -> bool:
    t = board.copy(stack=False); t.push(move)
    return t.is_check()


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


# ---------------------------- Workflows ---------------------------------------

def run_ladder(agents: List[str], rounds: int, k: float) -> Dict[str, object]:
    ratings: Dict[str, float] = {a: 1500.0 for a in agents}
    games: List[Dict[str, object]] = []
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a, b = agents[i], agents[j]
            for r in range(rounds):
                # A as white
                white = make_agent(a, chess.WHITE)
                black = make_agent(b, chess.BLACK)
                result, _moves = _play_game(white, black)
                if result == "1-0":
                    ratings[a], ratings[b] = _elo_update(ratings[a], ratings[b], 1.0, k)
                elif result == "0-1":
                    ratings[a], ratings[b] = _elo_update(ratings[a], ratings[b], 0.0, k)
                else:
                    ratings[a], ratings[b] = _elo_update(ratings[a], ratings[b], 0.5, k)
                games.append({"white": a, "black": b, "result": result, "round": r, "color": "Awhite"})
                # B as white
                white = make_agent(b, chess.WHITE)
                black = make_agent(a, chess.BLACK)
                result, _moves = _play_game(white, black)
                if result == "1-0":
                    ratings[b], ratings[a] = _elo_update(ratings[b], ratings[a], 1.0, k)
                elif result == "0-1":
                    ratings[b], ratings[a] = _elo_update(ratings[b], ratings[a], 0.0, k)
                else:
                    ratings[b], ratings[a] = _elo_update(ratings[b], ratings[a], 0.5, k)
                games.append({"white": b, "black": a, "result": result, "round": r, "color": "Bwhite"})
    return {"k_factor": k, "rounds": rounds, "ratings": ratings, "games": games}


def run_suites(agents: List[str], suite_paths: List[Path], limit: int) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for sp in suite_paths:
        per_agent: Dict[str, Dict[str, object]] = {}
        puzzles = list(_iter_puzzles(sp))
        if limit and len(puzzles) > limit:
            puzzles = puzzles[:limit]
        for agent_name in agents:
            total = 0
            ok = 0
            for pz in puzzles:
                board = chess.Board(pz.fen)
                agent = make_agent(agent_name, board.turn)
                move = _safe_choose_move(agent, board)
                if move is None or not board.is_legal(move):
                    success = False
                else:
                    judge = JUDGES.get(pz.judge)
                    success = judge(board, move) if judge else False
                total += 1
                ok += int(success)
            per_agent[agent_name] = {
                "total": total,
                "ok": ok,
                "accuracy": (ok / total) if total else 0.0,
            }
        result[str(sp)] = {"per_agent": per_agent}
    return result


def run_ab(pairs: List[Tuple[str, str]], games: int, k: Optional[float] = None) -> Dict[str, object]:
    per_pair: Dict[str, Dict[str, object]] = {}
    for a, b in pairs:
        w = l = d = 0
        games_white = games // 2
        games_black = games - games_white
        # A as white
        for _ in range(games_white):
            white = make_agent(a, chess.WHITE)
            black = make_agent(b, chess.BLACK)
            res, _ = _play_game(white, black)
            if res == "1-0":
                w += 1
            elif res == "0-1":
                l += 1
            else:
                d += 1
        # A as black
        for _ in range(games_black):
            white = make_agent(b, chess.WHITE)
            black = make_agent(a, chess.BLACK)
            res, _ = _play_game(white, black)
            if res == "1-0":
                l += 1
            elif res == "0-1":
                w += 1
            else:
                d += 1
        key = f"{a}_vs_{b}"
        per_pair[key] = {
            "A": a,
            "B": b,
            "wins": w,
            "losses": l,
            "draws": d,
            "win_rate": (w + 0.5 * d) / max(1, (w + l + d)),
        }
    return {"per_pair": per_pair}


# ---------------------------- Deltas ------------------------------------------

def compute_deltas(current: Dict[str, object], baseline: Dict[str, object]) -> Dict[str, object]:
    out = json.loads(json.dumps(current))  # deep copy

    # Ladder deltas per agent rating
    try:
        cur_ratings = (current.get("ladder") or {}).get("ratings", {})  # type: ignore
        base_ratings = (baseline.get("ladder") or {}).get("ratings", {})  # type: ignore
        deltas = {a: (cur_ratings.get(a, 0.0) - base_ratings.get(a, 0.0)) for a in cur_ratings}
        out.setdefault("ladder", {}).update({"deltas": deltas})  # type: ignore
    except Exception:
        pass

    # Suites deltas per agent accuracy per suite
    try:
        cur_suites = current.get("suites", {})  # type: ignore
        base_suites = baseline.get("suites", {})  # type: ignore
        suites_delta: Dict[str, Dict[str, float]] = {}
        for sp, payload in cur_suites.items():  # type: ignore
            cur_per_agent = payload.get("per_agent", {})
            base_per_agent = (base_suites.get(sp) or {}).get("per_agent", {})
            suites_delta[sp] = {
                a: (cur_per_agent.get(a, {}).get("accuracy", 0.0) - base_per_agent.get(a, {}).get("accuracy", 0.0))
                for a in cur_per_agent
            }
        out.setdefault("suites", {})  # type: ignore
        for sp, delta in suites_delta.items():  # type: ignore
            out["suites"].setdefault(sp, {}).update({"deltas": delta})  # type: ignore
    except Exception:
        pass

    # AB deltas per pair win_rate
    try:
        cur_pairs = (current.get("ab") or {}).get("per_pair", {})  # type: ignore
        base_pairs = (baseline.get("ab") or {}).get("per_pair", {})  # type: ignore
        ab_delta = {
            k: (cur_pairs.get(k, {}).get("win_rate", 0.0) - base_pairs.get(k, {}).get("win_rate", 0.0))
            for k in cur_pairs
        }
        out.setdefault("ab", {}).update({"deltas": ab_delta})  # type: ignore
    except Exception:
        pass

    return out


# ---------------------------- CLI ---------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Unified benchmark harness for chess agents")
    p.add_argument("--tasks", default="ladder,suites,ab", help="Comma-separated tasks: ladder,suites,ab")
    p.add_argument("--agents", default="DynamicBot,AggressiveBot,FortifyBot", help="Comma-separated agent names")
    p.add_argument("--rounds", type=int, default=4, help="Ladder: games per color per pairing")
    p.add_argument("--k-factor", type=float, default=24.0, dest="k", help="Ladder: Elo K factor")
    p.add_argument("--suites", default="puzzles/themes/mate_in_1.jsonl,puzzles/endgames/minimal.jsonl", help="Suites: JSONL or directory paths, comma-separated")
    p.add_argument("--limit", type=int, default=0, help="Suites: limit puzzles per suite (0=all)")
    p.add_argument("--games", type=int, default=12, help="AB: games per pair (both colors combined)")
    p.add_argument("--pairs", default="", help="AB: pairs as A:B,A2:B2. Defaults to first two agents if empty")
    p.add_argument("--runs", default="output", help="Directory to save JSON results")
    p.add_argument("--baseline", help="Path to previous bench JSON for delta computation")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    available = set(get_agent_names())
    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    unknown = [a for a in agents if a not in available]
    if unknown:
        print(f"Unknown agents: {unknown}. Available: {sorted(available)}")
        return 2

    tasks = {t.strip() for t in args.tasks.split(",") if t.strip()}

    payload: Dict[str, object] = {
        "schema_version": 1,
        "task": "bench",
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "agents": agents,
        "config": {
            "tasks": sorted(tasks),
            "rounds": args.rounds,
            "k_factor": args.k,
            "games": args.games,
            "suites": args.suites,
            "limit": args.limit,
        },
    }

    # Ladder
    if "ladder" in tasks:
        payload["ladder"] = run_ladder(agents, args.rounds, args.k)

    # Suites
    if "suites" in tasks:
        suite_paths = [Path(s.strip()) for s in args.suites.split(",") if s.strip()]
        payload["suites"] = run_suites(agents, suite_paths, args.limit)

    # AB
    if "ab" in tasks:
        if args.pairs:
            pairs: List[Tuple[str, str]] = []
            for item in args.pairs.split(","):
                if ":" in item:
                    a, b = item.split(":", 1)
                    pairs.append((a.strip(), b.strip()))
        else:
            if len(agents) < 2:
                print("AB requested but fewer than 2 agents provided")
                return 2
            pairs = [(agents[0], agents[1])]
        payload["ab"] = run_ab(pairs, args.games)

    # Baseline deltas
    if args.baseline:
        try:
            base_data = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
            payload = compute_deltas(payload, base_data)  # type: ignore
        except Exception as e:
            print(f"Warning: failed to load baseline '{args.baseline}': {e}")

    # Save
    Path(args.runs).mkdir(parents=True, exist_ok=True)
    ts = payload.get("timestamp") or datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.runs) / f"bench_{ts}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print concise summaries
    print(f"Saved: {out_path}")
    if "ladder" in payload:
        ladder = payload["ladder"]  # type: ignore
        ratings = ladder.get("ratings", {})  # type: ignore
        print("Ladder ratings:")
        for a in sorted(ratings, key=ratings.get, reverse=True):  # type: ignore
            print(f"  {a:>14}: {ratings[a]:7.1f}")
        if ladder.get("deltas"):
            print("  Deltas vs baseline:")
            for a, dv in ladder["deltas"].items():  # type: ignore
                print(f"    {a:>12}: {dv:+.1f}")
    if "suites" in payload:
        print("Suites accuracy per agent:")
        suites = payload["suites"]  # type: ignore
        for sp, data in suites.items():  # type: ignore
            pa = data.get("per_agent", {})  # type: ignore
            print(f"  {sp}:")
            for a, rec in pa.items():  # type: ignore
                print(f"    {a:>14}: {(rec['accuracy']*100):5.1f}% ({rec['ok']}/{rec['total']})")
            if data.get("deltas"):
                print("    Deltas vs baseline:")
                for a, dv in data["deltas"].items():  # type: ignore
                    print(f"      {a:>12}: {dv:+.3f}")
    if "ab" in payload:
        print("A/B head-to-head:")
        ab = payload["ab"]  # type: ignore
        for key, rec in ab.get("per_pair", {}).items():  # type: ignore
            wr = rec.get("win_rate", 0.0)
            print(f"  {key}: WR={(wr*100):.1f}%  W{rec['wins']}/L{rec['losses']}/D{rec['draws']}")
        if ab.get("deltas"):
            print("  Deltas vs baseline:")
            for k, dv in ab["deltas"].items():  # type: ignore
                print(f"    {k}: {dv:+.3f}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
