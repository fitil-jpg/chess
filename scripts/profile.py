#!/usr/bin/env python3
"""Profiling harness with cProfile and optional py-spy flamegraphs.

Usage:
  # cProfile evaluator.mobility on random positions
  python scripts/profile.py --target mobility --iters 2000 --out output/profile.prof

  # Run a mini-ladder and profile the run function
  python scripts/profile.py --target ladder --agents DynamicBot,AggressiveBot --rounds 2 --out output/ladder.prof

  # Generate a flamegraph with py-spy (if installed)
  python scripts/profile.py --py-spy --target ladder --agents DynamicBot,AggressiveBot --rounds 2 --flame output/ladder.svg
"""
from __future__ import annotations

import argparse
import cProfile
import pstats
from pathlib import Path
import sys
from pathlib import Path as _P

ROOT = _P(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chess

from scripts.bench import run_ladder  # type: ignore
from core.evaluator import Evaluator  # type: ignore


def _profile_cprofile(callable_fn, out_path: Path):
    pr = cProfile.Profile()
    pr.enable()
    try:
        callable_fn()
    finally:
        pr.disable()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pr.dump_stats(str(out_path))
        print(f"Saved profile: {out_path}")
        s = pstats.Stats(pr).sort_stats("cumtime")
        s.print_stats(20)


def _profile_pyspy(py_args: list[str], flame_out: Path):
    import subprocess
    flame_out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "py-spy", "record",
        "--format", "flamegraph",
        "--output", str(flame_out),
    ] + py_args
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Saved flamegraph: {flame_out}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Profiling harness")
    p.add_argument("--target", choices=["mobility", "ladder"], default="mobility")
    p.add_argument("--iters", type=int, default=2000)
    p.add_argument("--agents", default="DynamicBot,AggressiveBot")
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--out", default="output/profile.prof")
    p.add_argument("--py-spy", action="store_true")
    p.add_argument("--flame", default="output/flame.svg")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    out_path = Path(args.out)

    if args.py_spy:
        py_args = [sys.executable, __file__, "--target", args.target]
        if args.target == "mobility":
            py_args += ["--iters", str(args.iters), "--out", str(out_path)]
        else:
            py_args += [
                "--agents", args.agents,
                "--rounds", str(args.rounds),
                "--out", str(out_path),
            ]
        _profile_pyspy(py_args, Path(args.flame))
        return 0

    if args.target == "mobility":
        def _work():
            b = chess.Board()
            ev = Evaluator(b)
            total = 0
            for _ in range(args.iters):
                total += ev.mobility(b)[0]
            return total
        _profile_cprofile(_work, out_path)
        return 0

    if args.target == "ladder":
        agents = [a.strip() for a in args.agents.split(",") if a.strip()]
        def _work():
            run_ladder(agents, rounds=args.rounds, k=24.0)
        _profile_cprofile(_work, out_path)
        return 0

    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

