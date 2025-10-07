#!/usr/bin/env python3
"""Hyperparameter tuning harness for heuristics.

Features:
- Deterministic seeds via --seed (propagated to random, numpy, torch if available)
- Grid search, random search, and simple evolutionary (1+lambda) strategy
- Objective can be one of: ladder Elo (subset), suites accuracy, or mixed
- Parameters supported via environment variables consumed by bots/evaluator
  (e.g., CHESS_EVAL_*; CHESS_FORTIFY_*; CHESS_SCORER_*)

Examples:
  # Grid search over Fortify weights and Evaluator penalties
  python scripts/tune.py \
    --strategy grid \
    --param CHESS_FORTIFY_defense_density=3:7:2 \
    --param CHESS_EVAL_ISOLATED_PENALTY=-20:-5:5 \
    --objective suites \
    --suites puzzles/themes/mate_in_1.jsonl \
    --agents DynamicBot \
    --limit 100

  # Random search with fixed budget
  python scripts/tune.py --strategy random --budget 50 --objective ladder --agents DynamicBot,AggressiveBot

  # Evolutionary
  python scripts/tune.py --strategy evo --budget 40 --lambda 6 --sigma 0.3 --center CHESS_FORTIFY_defense_density=5
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import sys
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chess  # noqa: F401

from scripts.bench import run_ladder, run_suites  # type: ignore
from chess_ai.bot_agent import get_agent_names  # type: ignore


def _set_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np  # type: ignore
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch  # type: ignore
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def _parse_param(s: str):
    # Formats:
    #  key=val               → fixed
    #  key=min:max:step      → grid inclusive
    #  key~min:max           → random uniform float
    #  key|min:max           → random integer
    if "=" in s:
        k, v = s.split("=", 1)
        if ":" in v and v.count(":") == 2:
            a, b, step = v.split(":")
            return (k, ("grid", float(a), float(b), float(step)))
        else:
            return (k, ("fixed", v))
    if "~" in s:
        k, v = s.split("~", 1)
        a, b = v.split(":", 1)
        return (k, ("randf", float(a), float(b)))
    if "|" in s:
        k, v = s.split("|", 1)
        a, b = v.split(":", 1)
        return (k, ("randi", int(a), int(b)))
    raise ValueError(f"Bad --param format: {s}")


def _grid_values(a: float, b: float, step: float):
    n = int(math.floor((b - a) / step))
    return [a + i * step for i in range(n + 1)]


def _evaluate_objective(objective: str, agents: List[str], suites: List[Path], limit: int) -> float:
    if objective == "ladder":
        res = run_ladder(agents, rounds=2, k=24.0)
        # Sum of ratings as a simple scalar; higher is better
        ratings = res["ratings"]  # type: ignore
        return float(sum(ratings.values()))
    if objective == "suites":
        res = run_suites(agents, suites, limit)
        total = 0.0
        for _sp, payload in res.items():  # type: ignore
            for _a, rec in payload.get("per_agent", {}).items():  # type: ignore
                total += float(rec.get("accuracy", 0.0))
        return total
    if objective == "mixed":
        ladder = _evaluate_objective("ladder", agents, suites, limit)
        suites_val = _evaluate_objective("suites", agents, suites, limit)
        return ladder * 0.001 + suites_val
    raise ValueError("Unknown objective")


def _apply_env(env_overrides: Dict[str, str]):
    for k, v in env_overrides.items():
        os.environ[str(k)] = str(v)


def _strategy_grid(params: Dict[str, tuple], agents: List[str], suites: List[Path], limit: int, objective: str, seed: int):
    keys = list(params.keys())
    grids: List[List[Tuple[str, str]]] = []
    for k in keys:
        kind = params[k][0]
        if kind == "fixed":
            grids.append([(k, params[k][1])])
        elif kind == "grid":
            _, a, b, step = params[k]
            vals = _grid_values(a, b, step)
            grids.append([(k, str(int(v)) if float(v).is_integer() else str(v)) for v in vals])
        else:
            raise ValueError("Random-only params not allowed in grid strategy")

    best_score = -float("inf")
    best_env: Dict[str, str] = {}
    def _recurse(i: int, cur: List[Tuple[str, str]]):
        nonlocal best_score, best_env
        if i == len(grids):
            env = dict(cur)
            _set_seed(seed)
            _apply_env(env)
            score = _evaluate_objective(objective, agents, suites, limit)
            if score > best_score:
                best_score = score
                best_env = env.copy()
            return
        for kv in grids[i]:
            cur.append(kv)
            _recurse(i + 1, cur)
            cur.pop()
    _recurse(0, [])
    return best_score, best_env


def _strategy_random(params: Dict[str, tuple], budget: int, agents: List[str], suites: List[Path], limit: int, objective: str, seed: int):
    _set_seed(seed)
    best_score = -float("inf")
    best_env: Dict[str, str] = {}
    keys = list(params.keys())
    for _ in range(budget):
        env: Dict[str, str] = {}
        for k in keys:
            kind = params[k][0]
            if kind == "fixed":
                env[k] = str(params[k][1])
            elif kind == "randf":
                _, a, b = params[k]
                env[k] = str(random.uniform(a, b))
            elif kind == "randi":
                _, a, b = params[k]
                env[k] = str(random.randint(a, b))
            elif kind == "grid":
                _, a, b, step = params[k]
                vals = _grid_values(a, b, step)
                env[k] = str(random.choice(vals))
            else:
                raise ValueError("bad kind")
        _apply_env(env)
        score = _evaluate_objective(objective, agents, suites, limit)
        if score > best_score:
            best_score, best_env = score, env.copy()
    return best_score, best_env


def _strategy_evo(params: Dict[str, tuple], budget: int, lam: int, sigma: float, center: Dict[str, str], agents: List[str], suites: List[Path], limit: int, objective: str, seed: int):
    _set_seed(seed)
    # Start at center (or zeros) and mutate continuous params
    cur = center.copy()
    # Initialize fixed/defaults
    for k, spec in params.items():
        if k not in cur:
            if spec[0] == "fixed":
                cur[k] = str(spec[1])
            elif spec[0] == "grid":
                _, a, b, step = spec
                cur[k] = str(_grid_values(a, b, step)[0])
            elif spec[0] in ("randf", "randi"):
                cur[k] = str(spec[1])
    best_score = -float("inf")
    best_env = cur.copy()
    iters = max(1, budget // max(1, lam))
    for _ in range(iters):
        # Evaluate parent
        _apply_env(cur)
        parent_score = _evaluate_objective(objective, agents, suites, limit)
        if parent_score > best_score:
            best_score, best_env = parent_score, cur.copy()
        # Generate children
        children: List[Dict[str, str]] = []
        for _c in range(lam):
            child = cur.copy()
            for k, spec in params.items():
                if spec[0] in ("grid", "fixed"):
                    continue
                if spec[0] == "randi":
                    a, b = spec[1], spec[2]
                    base = int(child.get(k, a))
                    noise = int(round(random.gauss(0, sigma * (b - a))))
                    child[k] = str(max(a, min(b, base + noise)))
                elif spec[0] == "randf":
                    a, b = spec[1], spec[2]
                    try:
                        base = float(child.get(k, a))
                    except Exception:
                        base = a
                    noise = random.gauss(0, sigma * (b - a))
                    child[k] = str(max(a, min(b, base + noise)))
            children.append(child)
        # Select best child
        for ch in children:
            _apply_env(ch)
            sc = _evaluate_objective(objective, agents, suites, limit)
            if sc >= parent_score:
                cur = ch
                parent_score = sc
            if sc > best_score:
                best_score, best_env = sc, ch.copy()
    return best_score, best_env


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Hyperparameter tuning harness for heuristics")
    p.add_argument("--strategy", choices=["grid", "random", "evo"], default="random")
    p.add_argument("--param", action="append", default=[], help="Parameter spec, see docstring")
    p.add_argument("--budget", type=int, default=30, help="Iterations for random/evo")
    p.add_argument("--lambda", dest="lam", type=int, default=6, help="Children per evo iteration")
    p.add_argument("--sigma", type=float, default=0.2, help="Mutation scale (fraction of range)")
    p.add_argument("--center", action="append", default=[], help="key=value seeds for evo center")
    p.add_argument("--objective", choices=["ladder", "suites", "mixed"], default="suites")
    p.add_argument("--agents", default="DynamicBot", help="Comma-separated agent names")
    p.add_argument("--suites", default="puzzles/themes/mate_in_1.jsonl", help="Suites paths")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--runs", default="output")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    available = set(get_agent_names())
    unknown = [a for a in agents if a not in available]
    if unknown:
        print(f"Unknown agents: {unknown}. Available: {sorted(available)}")
        return 2

    params_list = [
        _parse_param(s) for s in args.param
    ]
    params = {k: v for k, v in params_list}
    suites = [Path(s.strip()) for s in args.suites.split(",") if s.strip()]

    center: Dict[str, str] = {}
    for c in args.center:
        k, v = c.split("=", 1)
        center[k] = v

    if args.strategy == "grid":
        score, env = _strategy_grid(params, agents, suites, args.limit, args.objective, args.seed)
    elif args.strategy == "random":
        score, env = _strategy_random(params, args.budget, agents, suites, args.limit, args.objective, args.seed)
    else:
        score, env = _strategy_evo(params, args.budget, args.lam, args.sigma, center, agents, suites, args.limit, args.objective, args.seed)

    Path(args.runs).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = {
        "schema_version": 1,
        "task": "tune",
        "timestamp": ts,
        "strategy": args.strategy,
        "objective": args.objective,
        "agents": agents,
        "best_score": score,
        "best_env": env,
    }
    out_path = Path(args.runs) / f"tune_{ts}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    print("Best:")
    for k, v in sorted(env.items()):
        print(f"  {k}={v}")
    print(f"Score={score}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

