#!/usr/bin/env python3
"""
Headless sequential tournament runner (no threading).

- Prints each pairing and per-game result as they happen
- Maintains and prints a live standings table in the terminal
- Supports simple round-robin (every agent plays every other agent)
- Supports best-of-N series (odd N) or a fixed number of games per pairing

Examples:
  python scripts/tournament.py --agents DynamicBot,FortifyBot,AggressiveBot --bo 3
  python scripts/tournament.py --agents NeuralBot,FortifyBot,AggressiveBot,EndgameBot --games 2

Notes:
- Scoring: win=1.0, draw=0.5, loss=0.0
- Colors alternate by game within a series
- Technical loss on illegal move/agent error/returned None
"""
from __future__ import annotations

import argparse
import traceback
import itertools
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import math
from pathlib import Path
from datetime import datetime, timezone
import time
import json
import threading

# Fix sys.path so stdlib modules are not shadowed by 'scripts/'
SCRIPT_DIR = os.path.dirname(__file__)
if SCRIPT_DIR in sys.path:
    try:
        sys.path.remove(SCRIPT_DIR)
    except ValueError:
        pass

# Ensure project root is importable when running as a script
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import chess

from chess_ai.bot_agent import make_agent, get_agent_names
from chess_ai.pattern_detector import PatternDetector as _PatternDetector, ChessPattern as _DetectedPattern
from evaluation import evaluate

# --- Runtime diagnostics for last game/move ---
# LAST_MOVE_STATUS is a short-lived status set by move selection helpers
# for the most recent agent call. Structure:
#   {"kind": "ok"|"timeout"|"agent_error", "error": str | None}
LAST_MOVE_STATUS: Optional[Dict[str, object]] = None

# LAST_GAME_META is populated by play_single_game when a technical loss occurs.
# Structure example (keys optional depending on failure kind):
#   {
#     "kind": "timeout"|"illegal_move"|"agent_error",
#     "side": "white"|"black",
#     "agent": str,
#     "move_uci": str,
#     "elapsed": float,
#     "budget": float,
#     "error": str,
#   }
LAST_GAME_META: Optional[Dict[str, object]] = None


class TournamentProgress:
    """Tracks and prints tournament-level progress and elapsed time."""

    def __init__(self, total_games_estimate: int) -> None:
        self.started_at_monotonic = time.monotonic()
        self.total_games_estimate = int(total_games_estimate)
        self.games_played = 0

    def _fmt_elapsed(self) -> str:
        secs = int(time.monotonic() - self.started_at_monotonic)
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def print_status(self, upcoming_white: str, upcoming_black: str) -> None:
        nxt = self.games_played + 1
        total = self.total_games_estimate
        approx = f"{nxt}/{total}" if total > 0 else f"{nxt}"
        print(f"[Турнір {approx}] Час минув: {self._fmt_elapsed()} | Наступна гра: {upcoming_white} (білі) — {upcoming_black} (чорні)")

    def increment(self) -> None:
        self.games_played += 1


class TournamentPatternsWriter:
    """Writes detected patterns from tournament games into a dedicated directory."""

    def __init__(self, outdir: Path, subdir_name: str = "patterns") -> None:
        self.base = outdir / subdir_name
        self.base.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.base / "patterns.jsonl"

    def log_patterns(
        self,
        *,
        a: str,
        b: str,
        white: str,
        black: str,
        game_index: int,
        ply_index: int,
        patterns: List[_DetectedPattern],
    ) -> None:
        if not patterns:
            return
        ts = datetime.now(timezone.utc).isoformat()
        with open(self.jsonl_path, "a", encoding="utf-8") as fh:
            for p in patterns:
                try:
                    payload: Dict[str, object] = {
                        "timestamp": ts,
                        "pair": {"a": a, "b": b},
                        "white": white,
                        "black": black,
                        "game_index": int(game_index),
                        "ply_index": int(ply_index),
                        "pattern": p.to_dict(),
                    }
                    fh.write(json.dumps(payload, ensure_ascii=False))
                    fh.write("\n")
                except Exception:
                    # Never let logging fail
                    continue

@dataclass
class PlayerStats:
    name: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    points: float = 0.0

    def record(self, result: str, as_white: bool) -> None:
        # result is "1-0", "0-1", or "1/2-1/2"
        self.played += 1
        if result == "1-0":
            if as_white:
                self.wins += 1; self.points += 1.0
            else:
                self.losses += 1
        elif result == "0-1":
            if as_white:
                self.losses += 1
            else:
                self.wins += 1; self.points += 1.0
        else:
            self.draws += 1; self.points += 0.5


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sequential headless tournament runner (RR or SE)")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["rr", "se"],
        default="rr",
        help="Tournament mode: rr (round-robin) or se (single-elimination)",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default="DynamicBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,RandomBot",
        help="Comma-separated list of agent names (see chess_ai.bot_agent.get_agent_names)",
    )
    dyn_group = parser.add_mutually_exclusive_group()
    dyn_group.add_argument(
        "--include-dynamic",
        action="store_true",
        help="Ensure DynamicBot is included in the agents list",
    )
    dyn_group.add_argument(
        "--exclude-dynamic",
        action="store_true",
        help="Remove DynamicBot from the agents list",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=None,
        help="Number of games per pairing (overrides --bo if set). Default depends on --bo (3 if omitted).",
    )
    parser.add_argument(
        "--bo",
        type=int,
        default=3,
        choices=[1, 3, 5, 7],
        help="Best-of-N series length for each pairing (odd)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["bo3", "bo5", "bo7"],
        help="Series format; overrides --bo when provided",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=600,
        help="Safety cap: maximum plies per game (to avoid infinite games)",
    )
    parser.add_argument(
        "--time",
        type=int,
        default=60,
        help="Per-move time limit in seconds (0 disables)",
    )
    parser.add_argument(
        "--clock",
        type=str,
        default=None,
        help="Per-player chess clock in the form 'M|inc', e.g., 1|0 for 1+0 blitz. Overrides --time when provided.",
    )
    parser.add_argument(
        "--tiebreaks",
        type=str,
        choices=["on", "off"],
        default="on",
        help="Tie-breaks on tie: two 1|0 blitz games, then Armageddon (W 60s vs B 45s, draw → Black)",
    )
    parser.add_argument(
        "--out-root",
        type=str,
        default="output/tournaments",
        help="Directory to place timestamped tournament outputs (default: output/tournaments)",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optional tag to include in metadata for easier identification",
    )
    return parser.parse_args(argv)


def print_pairing_header(a: str, b: str, series_len: int) -> None:
    print(f"\n=== Пара: {a} vs {b} | Серія: {series_len} ігор ===")


def print_game_header(idx: int, white: str, black: str) -> None:
    print(f"Гра {idx}: {white} (білі) — {black} (чорні)")


def print_game_result(result: str) -> None:
    tag = {
        "1-0": "Перемога білих",
        "0-1": "Перемога чорних",
        "1/2-1/2": "Нічия",
    }.get(result, result)
    # If the last game ended via technical loss, append concise reason
    reason_suffix = ""
    try:
        if result in ("1-0", "0-1") and LAST_GAME_META and LAST_GAME_META.get("kind"):
            k = str(LAST_GAME_META.get("kind"))
            side = str(LAST_GAME_META.get("side", "?"))
            agent = str(LAST_GAME_META.get("agent", "?"))
            if k == "timeout":
                reason_suffix = f" | тех. поразка: TIMEOUT ({side}, {agent})"
            elif k == "illegal_move":
                mv = LAST_GAME_META.get("move_uci")
                reason_suffix = f" | тех. поразка: ILLEGAL MOVE {mv} ({side}, {agent})"
            elif k == "agent_error":
                err = str(LAST_GAME_META.get("error", ""))
                if len(err) > 120:
                    err = err[:117] + "..."
                reason_suffix = f" | тех. поразка: ERROR ({side}, {agent}) {err}"
    except Exception:
        # Never let logging fail
        reason_suffix = ""
    print(f"Результат: {result} ({tag}){reason_suffix}")


def print_standings(standings: Dict[str, PlayerStats]) -> None:
    print("\nПоточна турнірна таблиця:")
    # Sort by points desc, then wins desc, then name
    ordered = sorted(standings.values(), key=lambda s: (-s.points, -s.wins, s.name))
    # Compute max widths for nice alignment
    name_w = max(5, max(len(s.name) for s in ordered))
    header = f"{'Місце':>5}  {'Гравець':<{name_w}}  {'Очки':>5}  {'W':>3}  {'D':>3}  {'L':>3}  {'Ігор':>4}"
    print(header)
    print("-" * len(header))
    for i, s in enumerate(ordered, start=1):
        print(
            f"{i:>5}  {s.name:<{name_w}}  {s.points:>5.1f}  {s.wins:>3}  {s.draws:>3}  {s.losses:>3}  {s.played:>4}"
        )


class TournamentOutputWriter:
    """Manages writing live bracket and per-game logs to a timestamped directory."""

    def __init__(self, out_root: Path, tag: Optional[str] = None) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.outdir = out_root / timestamp
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.bracket_path = self.outdir / "bracket.json"
        self.logs_path = self.outdir / "match_logs.jsonl"
        self.summary_path = self.outdir / "summary.txt"
        self.tag = tag

        self._pairs: Dict[str, Dict[str, object]] = {}
        self.bracket: Dict[str, object] = {
            "type": "",
            "format": "",
            "agents": [],
            "games_per_pair": None,
            "tiebreaks": False,
            "max_plies": None,
            "time_per_move": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "tag": tag,
            "pairs": [],
            "seeds": [],
            "rounds": [],
        }
        # Initialize on disk
        self._write_bracket()

    def set_round_robin_metadata(
        self,
        *,
        agents: List[str],
        format_label: str,
        games_per_pair: int,
        tiebreaks: bool,
        max_plies: int,
        time_per_move: Optional[int],
        clock_initial: Optional[float] = None,
        clock_increment: Optional[float] = None,
    ) -> None:
        self.bracket["type"] = "round_robin"
        self.bracket["format"] = format_label
        self.bracket["agents"] = list(agents)
        self.bracket["games_per_pair"] = int(games_per_pair)
        self.bracket["tiebreaks"] = bool(tiebreaks)
        self.bracket["max_plies"] = int(max_plies)
        self.bracket["time_per_move"] = int(time_per_move) if time_per_move else None
        # Optional per-player clock
        self.bracket["clock_initial"] = float(clock_initial) if clock_initial else None
        self.bracket["clock_increment"] = float(clock_increment) if clock_increment else None
        self._touch_and_write()

    def ensure_pair(self, a: str, b: str) -> None:
        key = f"{a}__vs__{b}"
        if key not in self._pairs:
            self._pairs[key] = {
                "a": a,
                "b": b,
                "results": [],
                "points_a": 0.0,
                "points_b": 0.0,
            }
            self._sync_pairs_and_write()

    def update_pair(self, a: str, b: str, results: List[str], pts_a: float, pts_b: float) -> None:
        key = f"{a}__vs__{b}"
        self._pairs[key] = {
            "a": a,
            "b": b,
            "results": list(results),
            "points_a": float(pts_a),
            "points_b": float(pts_b),
        }
        self._sync_pairs_and_write()

    def log_game(
        self,
        *,
        a: str,
        b: str,
        white: str,
        black: str,
        game_index: int,
        result: str,
        tiebreak: bool = False,
        meta: Optional[Dict[str, object]] = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pair": {"a": a, "b": b},
            "game_index": int(game_index),
            "white": white,
            "black": black,
            "result": result,
            "tiebreak": bool(tiebreak),
        }
        if meta is not None:
            try:
                # Ensure JSON-serializable, fall back to str on failure per field
                safe_meta: Dict[str, object] = {}
                for k, v in meta.items():
                    try:
                        json.dumps(v)
                        safe_meta[k] = v
                    except Exception:
                        safe_meta[k] = str(v)
                entry["meta"] = safe_meta
            except Exception:
                entry["meta"] = {"error": "failed to serialize meta"}
        with open(self.logs_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry))
            f.write("\n")

    def write_summary(self, standings: Dict[str, PlayerStats]) -> None:
        # Build a simple aligned table similar to print_standings
        ordered = sorted(standings.values(), key=lambda s: (-s.points, -s.wins, s.name))
        name_w = max(5, max(len(s.name) for s in ordered)) if ordered else 5
        header = f"{'Місце':>5}  {'Гравець':<{name_w}}  {'Очки':>5}  {'W':>3}  {'D':>3}  {'L':>3}  {'Ігор':>4}"
        lines: List[str] = []
        lines.append("Фінальна таблиця:")
        lines.append(header)
        lines.append("-" * len(header))
        for i, s in enumerate(ordered, start=1):
            lines.append(
                f"{i:>5}  {s.name:<{name_w}}  {s.points:>5.1f}  {s.wins:>3}  {s.draws:>3}  {s.losses:>3}  {s.played:>4}"
            )
        self.summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _sync_pairs_and_write(self) -> None:
        self.bracket["pairs"] = list(self._pairs.values())
        self._touch_and_write()

    def _touch_and_write(self) -> None:
        self.bracket["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._write_bracket()

    def _write_bracket(self) -> None:
        with open(self.bracket_path, "w", encoding="utf-8") as f:
            json.dump(self.bracket, f, indent=2, ensure_ascii=False)

    # --- Single-elimination helpers ---
    def set_single_elimination_metadata(
        self,
        *,
        agents: List[str],
        format_label: str,
        tiebreaks: bool,
        max_plies: int,
        time_per_move: Optional[int],
        clock_initial: Optional[float] = None,
        clock_increment: Optional[float] = None,
        seeds: List[str],
    ) -> None:
        self.bracket["type"] = "single_elimination"
        self.bracket["format"] = format_label
        self.bracket["agents"] = list(agents)
        self.bracket["tiebreaks"] = bool(tiebreaks)
        self.bracket["max_plies"] = int(max_plies)
        self.bracket["time_per_move"] = int(time_per_move) if time_per_move else None
        self.bracket["clock_initial"] = float(clock_initial) if clock_initial else None
        self.bracket["clock_increment"] = float(clock_increment) if clock_increment else None
        self.bracket["pairs"] = []  # unused in SE
        self.bracket["seeds"] = list(seeds)
        self.bracket["rounds"] = []
        self._touch_and_write()

    def _get_or_create_round(self, round_name: str) -> Dict[str, object]:
        rounds: List[Dict[str, object]] = self.bracket.get("rounds", [])  # type: ignore[assignment]
        for r in rounds:
            if r.get("name") == round_name:
                return r
        new_round = {"name": round_name, "matches": []}
        rounds.append(new_round)
        self.bracket["rounds"] = rounds
        self._touch_and_write()
        return new_round

    def update_match(
        self,
        *,
        round_name: str,
        match_index: int,
        a: Optional[str],
        b: Optional[str],
        results: List[str],
        pts_a: float,
        pts_b: float,
        winner: Optional[str],
    ) -> None:
        r = self._get_or_create_round(round_name)
        matches: List[Dict[str, object]] = r["matches"]  # type: ignore[assignment]
        # Ensure list large enough
        while len(matches) <= match_index:
            matches.append({
                "a": None,
                "b": None,
                "results": [],
                "points_a": 0.0,
                "points_b": 0.0,
                "winner": None,
            })
        matches[match_index] = {
            "a": a,
            "b": b,
            "results": list(results),
            "points_a": float(pts_a),
            "points_b": float(pts_b),
            "winner": winner,
        }
        self._touch_and_write()

    def write_se_summary(self, champion: Optional[str]) -> None:
        lines: List[str] = []
        lines.append("Single-elimination results")
        if champion:
            lines.append(f"Champion: {champion}")
        # Compact overview of rounds
        for r in self.bracket.get("rounds", []):  # type: ignore[index]
            lines.append(f"\n{r.get('name')}")
            for idx, m in enumerate(r.get("matches", [])):
                a = m.get("a")
                b = m.get("b")
                pa = m.get("points_a")
                pb = m.get("points_b")
                w = m.get("winner")
                lines.append(f"  M{idx+1}: {a} vs {b} -> {pa}-{pb} | {w}")
        self.summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _choose_move_with_timeout(agent, board: chess.Board, timeout_s: Optional[int]):
    """Call agent.choose_move(board) with a soft timeout.

    Returns a chess.Move or None on timeout/error. Uses a daemon thread to avoid blocking.
    """
    global LAST_MOVE_STATUS
    if not timeout_s or timeout_s <= 0:
        try:
            mv = agent.choose_move(board)
            LAST_MOVE_STATUS = {"kind": "ok", "error": None}
            return mv
        except Exception as exc:
            # Agent crashed
            LAST_MOVE_STATUS = {"kind": "agent_error", "error": f"{type(exc).__name__}: {exc}"}
            return None

    result = {"move": None}
    done = threading.Event()
    status = {"kind": "ok", "error": None}

    # Work on a lightweight copy to avoid any accidental cross-thread mutations.
    board_copy = board.copy(stack=False)

    def _worker():
        try:
            mv = agent.choose_move(board_copy)
            result["move"] = mv
        except Exception as exc:
            result["move"] = None
            status["kind"] = "agent_error"
            # Capture concise exception summary for logs
            status["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            done.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    done.wait(timeout=timeout_s)
    if done.is_set():
        LAST_MOVE_STATUS = status
        return result["move"]
    else:
        LAST_MOVE_STATUS = {"kind": "timeout", "error": None}
        return None


def _choose_move_with_budget(agent, board: chess.Board, budget_s: float) -> Tuple[Optional[chess.Move], float, bool]:
    """Run agent.choose_move(board) on a copy with a hard budget.

    Returns (move or None, elapsed_seconds, finished_in_time).
    If finished_in_time is False, caller should treat as flag-fall.
    """
    global LAST_MOVE_STATUS
    if budget_s <= 0:
        LAST_MOVE_STATUS = {"kind": "timeout", "error": None}
        return None, 0.0, False

    result: Dict[str, Optional[chess.Move]] = {"move": None}
    done = threading.Event()
    board_copy = board.copy(stack=False)
    status = {"kind": "ok", "error": None}

    def _worker():
        try:
            mv = agent.choose_move(board_copy)
            result["move"] = mv
        except Exception as exc:
            result["move"] = None
            status["kind"] = "agent_error"
            status["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            done.set()

    t0 = time.monotonic()
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    finished = done.wait(timeout=budget_s)
    elapsed = time.monotonic() - t0
    if finished:
        LAST_MOVE_STATUS = status
    else:
        LAST_MOVE_STATUS = {"kind": "timeout", "error": None}
    return (result["move"] if finished else None), elapsed, finished


def play_single_game(
    white_agent_name: str,
    black_agent_name: str,
    *,
    max_plies: int,
    time_per_move: Optional[int] = None,
    clock_initial: Optional[float] = None,
    clock_increment: float = 0.0,
    clock_initial_white: Optional[float] = None,
    clock_initial_black: Optional[float] = None,
    # Optional tournament diagnostics
    detector: Optional[_PatternDetector] = None,
    patterns_writer: Optional["TournamentPatternsWriter"] = None,
    pair_a: Optional[str] = None,
    pair_b: Optional[str] = None,
    game_index: int = 0,
    progress: Optional["TournamentProgress"] = None,
) -> str:
    """Play one game and return chess result string: '1-0', '0-1', or '1/2-1/2'.
    Technical loss is applied if an agent returns None or makes illegal move.
    """
    board = chess.Board()
    white_agent = make_agent(white_agent_name, chess.WHITE)
    black_agent = make_agent(black_agent_name, chess.BLACK)
    # Reset last game diagnostics at start
    global LAST_GAME_META
    LAST_GAME_META = None

    try:
        # Per-player clock mode
        # Priority: explicit per-side initial clocks (e.g., Armageddon), otherwise symmetric initial
        if (clock_initial_white is not None) or (clock_initial_black is not None) or (clock_initial is not None and clock_initial > 0):
            init_w = float(clock_initial_white) if clock_initial_white is not None else (float(clock_initial) if clock_initial is not None else 0.0)
            init_b = float(clock_initial_black) if clock_initial_black is not None else (float(clock_initial) if clock_initial is not None else 0.0)
            time_left_w = init_w
            time_left_b = init_b

            while not board.is_game_over() and len(board.move_stack) < max_plies:
                mover_is_white = board.turn == chess.WHITE
                agent = white_agent if mover_is_white else black_agent
                budget = time_left_w if mover_is_white else time_left_b

                # Evaluation before move (for pattern detection)
                eval_before_total = None
                try:
                    eval_before_total, _ = evaluate(board)
                except Exception:
                    eval_before_total = None

                move, elapsed, finished = _choose_move_with_budget(agent, board, budget)
                # Deduct actual elapsed from mover's clock
                if mover_is_white:
                    time_left_w -= elapsed
                else:
                    time_left_b -= elapsed

                # Flag-fall if not finished in time or clock dipped below zero
                if not finished or (time_left_w < -1e-6 if mover_is_white else time_left_b < -1e-6):
                    LAST_GAME_META = {
                        "kind": "timeout",
                        "side": "white" if mover_is_white else "black",
                        "agent": white_agent_name if mover_is_white else black_agent_name,
                        "elapsed": float(elapsed),
                        "budget": float(budget),
                    }
                    return "0-1" if mover_is_white else "1-0"

                # If agent returned None despite finishing (error), technical loss
                if move is None:
                    # Determine agent error vs. no-move
                    kind = "agent_error"
                    err = None
                    if LAST_MOVE_STATUS and LAST_MOVE_STATUS.get("kind") == "agent_error":
                        kind = "agent_error"
                        err = LAST_MOVE_STATUS.get("error")
                    LAST_GAME_META = {
                        "kind": kind,
                        "side": "white" if mover_is_white else "black",
                        "agent": white_agent_name if mover_is_white else black_agent_name,
                        "elapsed": float(elapsed),
                        "budget": float(budget),
                        "error": err,
                    }
                    return "0-1" if mover_is_white else "1-0"

                # Validate legality before pushing
                if not board.is_legal(move):
                    try:
                        mv_uci = move.uci() if move is not None else None
                    except Exception:
                        mv_uci = None
                    LAST_GAME_META = {
                        "kind": "illegal_move",
                        "side": "white" if mover_is_white else "black",
                        "agent": white_agent_name if mover_is_white else black_agent_name,
                        "move_uci": mv_uci,
                    }
                    return "0-1" if mover_is_white else "1-0"
                try:
                    board.push(move)
                except Exception:
                    # Defensive: treat any push error as illegal
                    try:
                        mv_uci = move.uci() if move is not None else None
                    except Exception:
                        mv_uci = None
                    LAST_GAME_META = {
                        "kind": "illegal_move",
                        "side": "white" if mover_is_white else "black",
                        "agent": white_agent_name if mover_is_white else black_agent_name,
                        "move_uci": mv_uci,
                    }
                    return "0-1" if mover_is_white else "1-0"

                # Apply increment after a legal move
                if clock_increment > 0:
                    if mover_is_white:
                        time_left_w += clock_increment
                    else:
                        time_left_b += clock_increment

                # Pattern detection and logging
                if detector is not None and patterns_writer is not None and pair_a and pair_b:
                    try:
                        eval_after_total, _ = evaluate(board)
                    except Exception:
                        eval_after_total = None
                    try:
                        pat_before = {"total": eval_before_total} if eval_before_total is not None else {"total": 0}
                        pat_after = {"total": eval_after_total} if eval_after_total is not None else {"total": 0}
                        pats = detector.detect_patterns(
                            board,
                            move,
                            evaluation_before=pat_before,
                            evaluation_after=pat_after,
                            bot_analysis=None,
                        )
                        if pats:
                            patterns_writer.log_patterns(
                                a=pair_a,
                                b=pair_b,
                                white=white_agent_name,
                                black=black_agent_name,
                                game_index=game_index,
                                ply_index=len(board.move_stack),
                                patterns=pats,
                            )
                    except Exception:
                        pass

        else:
            # Legacy per-move timeout mode
            while not board.is_game_over() and len(board.move_stack) < max_plies:
                agent = white_agent if board.turn == chess.WHITE else black_agent
                # Eval before for pattern detection
                eval_before_total = None
                try:
                    eval_before_total, _ = evaluate(board)
                except Exception:
                    eval_before_total = None
                move = _choose_move_with_timeout(agent, board, time_per_move)
                if move is None:
                    # Immediate loss for side to move
                    mover_is_white = (board.turn == chess.WHITE)
                    kind = None
                    err = None
                    if LAST_MOVE_STATUS:
                        k = LAST_MOVE_STATUS.get("kind")
                        if k == "timeout":
                            kind = "timeout"
                        elif k == "agent_error":
                            kind = "agent_error"
                            err = LAST_MOVE_STATUS.get("error")
                    LAST_GAME_META = {
                        "kind": kind or "agent_error",
                        "side": "white" if mover_is_white else "black",
                        "agent": white_agent_name if mover_is_white else black_agent_name,
                        "error": err,
                        "budget": float(time_per_move) if time_per_move else None,
                    }
                    return "0-1" if mover_is_white else "1-0"
                # Validate legality before pushing
                mover_is_white = (board.turn == chess.WHITE)
                if not board.is_legal(move):
                    try:
                        mv_uci = move.uci() if move is not None else None
                    except Exception:
                        mv_uci = None
                    LAST_GAME_META = {
                        "kind": "illegal_move",
                        "side": "white" if mover_is_white else "black",
                        "agent": white_agent_name if mover_is_white else black_agent_name,
                        "move_uci": mv_uci,
                    }
                    return "0-1" if mover_is_white else "1-0"
                try:
                    board.push(move)
                except Exception:
                    # Defensive: treat any push error as illegal
                    try:
                        mv_uci = move.uci() if move is not None else None
                    except Exception:
                        mv_uci = None
                    LAST_GAME_META = {
                        "kind": "illegal_move",
                        "side": "white" if mover_is_white else "black",
                        "agent": white_agent_name if mover_is_white else black_agent_name,
                        "move_uci": mv_uci,
                    }
                    return "0-1" if mover_is_white else "1-0"
                # Pattern detection and logging
                if detector is not None and patterns_writer is not None and pair_a and pair_b:
                    try:
                        eval_after_total, _ = evaluate(board)
                    except Exception:
                        eval_after_total = None
                    try:
                        pat_before = {"total": eval_before_total} if eval_before_total is not None else {"total": 0}
                        pat_after = {"total": eval_after_total} if eval_after_total is not None else {"total": 0}
                        pats = detector.detect_patterns(
                            board,
                            move,
                            evaluation_before=pat_before,
                            evaluation_after=pat_after,
                            bot_analysis=None,
                        )
                        if pats:
                            patterns_writer.log_patterns(
                                a=pair_a,
                                b=pair_b,
                                white=white_agent_name,
                                black=black_agent_name,
                                game_index=game_index,
                                ply_index=len(board.move_stack),
                                patterns=pats,
                            )
                    except Exception:
                        pass
    except Exception:
        # Any unexpected exception from agent => their loss
        mover_is_white = (board.turn == chess.WHITE)
        # Capture traceback excerpt for diagnostics
        exc_str = traceback.format_exc(limit=1)
        LAST_GAME_META = {
            "kind": "agent_error",
            "side": "white" if mover_is_white else "black",
            "agent": white_agent_name if mover_is_white else black_agent_name,
            "error": exc_str.strip(),
        }
        return "0-1" if mover_is_white else "1-0"

    if board.is_game_over():
        LAST_GAME_META = None
        return board.result()
    # Safety draw if exceeded max plies
    LAST_GAME_META = None
    return "1/2-1/2"


def play_series(
    a: str,
    b: str,
    series_games: int,
    *,
    max_plies: int,
    time_per_move: Optional[int] = None,
    clock_initial: Optional[float] = None,
    clock_increment: float = 0.0,
    tiebreaks: bool = False,
    writer: Optional["TournamentOutputWriter"] = None,
) -> Tuple[float, float, List[str]]:
    """Play a series of games with alternating colors.
    Returns (points_a, points_b, list_of_results_in_order).
    If series_games is odd, early stop when one reaches majority.
    """
    results: List[str] = []
    pts_a = 0.0
    pts_b = 0.0
    needed = (series_games // 2) + 1 if series_games % 2 == 1 else None

    # Prepare live helpers
    detector = _PatternDetector()
    patterns_writer = TournamentPatternsWriter(writer.outdir) if writer is not None else None
    # Total games counter for round-robin status (approximate within this pair)
    progress = TournamentProgress(total_games_estimate=series_games)

    for i in range(series_games):
        white, black = (a, b) if i % 2 == 0 else (b, a)
        print_game_header(i + 1, white, black)
        res = play_single_game(
            white,
            black,
            max_plies=max_plies,
            time_per_move=time_per_move,
            clock_initial=clock_initial,
            clock_increment=clock_increment,
            detector=detector,
            patterns_writer=patterns_writer,
            pair_a=a,
            pair_b=b,
            game_index=i + 1,
            progress=progress,
        )
        print_game_result(res)
        results.append(res)
        progress.increment()

        # Per-game log and live bracket update
        if writer is not None:
            writer.log_game(a=a, b=b, white=white, black=black, game_index=i + 1, result=res, tiebreak=False, meta=LAST_GAME_META)

        # Update points
        if res == "1-0":
            if white == a:
                pts_a += 1.0
            else:
                pts_b += 1.0
        elif res == "0-1":
            if white == a:
                pts_b += 1.0
            else:
                pts_a += 1.0
        else:
            pts_a += 0.5
            pts_b += 0.5

        # Best-of early stop
        if needed is not None and (pts_a >= needed or pts_b >= needed):
            if writer is not None:
                writer.update_pair(a, b, results, pts_a, pts_b)
            break

        if writer is not None:
            writer.update_pair(a, b, results, pts_a, pts_b)

    # Tie-break sequence if the series ended tied on points
    if tiebreaks and abs(pts_a - pts_b) < 1e-9:
        print("Тай-брейки: 2 бліц-ігри 1|0; якщо рівність — Армагеддон (Білі 60s, Чорні 45s; нічия → Чорні)")

        # Two extra blitz games 1|0, alternating colors
        for _ in range(2):
            tiebreak_idx = len(results)
            white, black = (a, b) if tiebreak_idx % 2 == 0 else (b, a)
            print_game_header(tiebreak_idx + 1, white, black)
            res = play_single_game(
                white,
                black,
                max_plies=max_plies,
                time_per_move=None,  # force clock mode
                clock_initial=60.0,
                clock_increment=0.0,
                detector=detector,
                patterns_writer=patterns_writer,
                pair_a=a,
                pair_b=b,
                game_index=tiebreak_idx + 1,
                progress=progress,
            )
            print_game_result(res)
            results.append(res)
            if res == "1-0":
                if white == a:
                    pts_a += 1.0
                else:
                    pts_b += 1.0
            elif res == "0-1":
                if white == a:
                    pts_b += 1.0
                else:
                    pts_a += 1.0
            else:
                pts_a += 0.5
                pts_b += 0.5
            if writer is not None:
                writer.log_game(a=a, b=b, white=white, black=black, game_index=tiebreak_idx + 1, result=res, tiebreak=True, meta=LAST_GAME_META)
                writer.update_pair(a, b, results, pts_a, pts_b)

        # If still tied, Armageddon: W 60s vs B 45s, draw → Black
        if abs(pts_a - pts_b) < 1e-9:
            tiebreak_idx = len(results)
            white, black = (a, b) if tiebreak_idx % 2 == 0 else (b, a)
            print("Армагеддон: Білі 60s проти Чорних 45s; нічия рахується як перемога Чорних")
            print_game_header(tiebreak_idx + 1, white, black)
            res = play_single_game(
                white,
                black,
                max_plies=max_plies,
                time_per_move=None,
                clock_initial=None,
                clock_increment=0.0,
                clock_initial_white=60.0,
                clock_initial_black=45.0,
                detector=detector,
                patterns_writer=patterns_writer,
                pair_a=a,
                pair_b=b,
                game_index=tiebreak_idx + 1,
                progress=progress,
            )
            print_game_result(res)
            results.append(res)
            if writer is not None:
                writer.log_game(a=a, b=b, white=white, black=black, game_index=tiebreak_idx + 1, result=res, tiebreak=True, meta=LAST_GAME_META)
            if res == "1-0":
                if white == a:
                    pts_a += 1.0
                else:
                    pts_b += 1.0
            elif res == "0-1":
                if white == a:
                    pts_b += 1.0
                else:
                    pts_a += 1.0
            else:
                # Draw counts as a win for Black (award 1 point to Black side)
                if white == a:
                    pts_b += 1.0
                else:
                    pts_a += 1.0

    # Final bracket update for this pair
    if writer is not None:
        writer.update_pair(a, b, results, pts_a, pts_b)
    return pts_a, pts_b, results


def run_round_robin(
    agent_names: List[str],
    games_per_pair: int,
    *,
    max_plies: int,
    time_per_move: Optional[int] = None,
    clock_initial: Optional[float] = None,
    clock_increment: float = 0.0,
    tiebreaks: bool = False,
    writer: Optional["TournamentOutputWriter"] = None,
) -> Dict[str, PlayerStats]:
    standings: Dict[str, PlayerStats] = {name: PlayerStats(name) for name in agent_names}

    pairs = list(itertools.combinations(agent_names, 2))
    for a, b in pairs:
        print_pairing_header(a, b, games_per_pair)
        if writer is not None:
            writer.ensure_pair(a, b)
        pts_a, pts_b, series_results = play_series(
            a,
            b,
            games_per_pair,
            max_plies=max_plies,
            time_per_move=time_per_move,
            clock_initial=clock_initial,
            clock_increment=clock_increment,
            tiebreaks=tiebreaks,
            writer=writer,
        )

        # Per-game standings update with correct colors
        for i, res in enumerate(series_results):
            white, black = (a, b) if i % 2 == 0 else (b, a)
            standings[a].record(res, as_white=(white == a))
            standings[b].record(res, as_white=(white == b))
            print_standings(standings)

    return standings


def _find_latest_selfplay_elo_file(search_dir: Path) -> Optional[Path]:
    """Return the newest selfplay Elo JSON file in search_dir, if any.

    Filenames are of the form selfplay_elo_YYYYmmdd_HHMMSS.json, which
    sort lexicographically by timestamp, so name ordering is sufficient.
    """
    try:
        candidates = sorted(search_dir.glob("selfplay_elo_*.json"), key=lambda p: p.name)
    except Exception:
        candidates = []
    return candidates[-1] if candidates else None


def _load_latest_elo_ratings(search_dir: Path) -> Optional[Dict[str, float]]:
    """Load ratings from the most recent selfplay Elo JSON, if available.

    Returns a mapping from agent name to Elo rating, or None if unavailable.
    """
    latest = _find_latest_selfplay_elo_file(search_dir)
    if latest is None:
        return None
    try:
        with open(latest, "r", encoding="utf-8") as f:
            payload = json.load(f)
        raw = payload.get("ratings")
        if not isinstance(raw, dict):
            return None
        ratings: Dict[str, float] = {}
        for name, value in raw.items():
            try:
                ratings[str(name)] = float(value)
            except Exception:
                # Skip non-numeric entries gracefully
                continue
        if not ratings:
            return None
        print(f"Seeding from Elo file: {latest}")
        return ratings
    except Exception:
        return None


def _seed_bracket_participants(agent_names: List[str]) -> List[str]:
    """Return seed order for single-elimination.

    If a latest selfplay Elo JSON exists under ROOT/output, seed by
    descending Elo for the requested agents; otherwise, preserve input
    order.
    """
    ratings = _load_latest_elo_ratings(Path(ROOT) / "output")
    if not ratings:
        return list(agent_names)

    index_by_input_order = {name: idx for idx, name in enumerate(agent_names)}

    def sort_key(name: str) -> Tuple[float, int]:
        r = ratings.get(name)
        # Higher Elo first. Unrated agents are placed at the end, keeping input order.
        primary = -float(r) if isinstance(r, (int, float)) else float("inf")
        return (primary, index_by_input_order[name])

    seeds = sorted(agent_names, key=sort_key)
    # Brief preview for transparency
    try:
        ordered_preview = ", ".join(f"{n}({ratings.get(n, '?')})" for n in seeds)
        print(f"Seeds (high→low Elo): {ordered_preview}")
    except Exception:
        pass
    return seeds


def _round_name(num_players: int) -> str:
    if num_players >= 8 and ((num_players & (num_players - 1)) == 0):
        if num_players == 8:
            return "Quarterfinals"
        if num_players == 16:
            return "Round of 16"
        if num_players == 32:
            return "Round of 32"
    if num_players == 4:
        return "Semifinals"
    if num_players == 2:
        return "Final"
    return f"Round of {num_players}"


def run_single_elimination(
    agent_names: List[str],
    *,
    games_per_match: int,
    max_plies: int,
    time_per_move: Optional[int] = None,
    clock_initial: Optional[float] = None,
    clock_increment: float = 0.0,
    tiebreaks: bool = False,
    writer: Optional["TournamentOutputWriter"] = None,
) -> str:
    """Run a single-elimination bracket and return champion name.

    Pairings are seeded 1 vs N, 2 vs N-1, etc. Colors alternate by game.
    """
    assert len(agent_names) >= 2, "Need at least 2 agents for single-elimination"
    seeds = _seed_bracket_participants(agent_names)

    if writer is not None:
        fmt_label = f"Bo{games_per_match}" if games_per_match % 2 == 1 else f"{games_per_match} games"
        writer.set_single_elimination_metadata(
            agents=agent_names,
            format_label=fmt_label,
            tiebreaks=tiebreaks,
            max_plies=max_plies,
            time_per_move=time_per_move,
            clock_initial=clock_initial,
            clock_increment=clock_increment,
            seeds=seeds,
        )

    current = list(seeds)
    round_idx = 0
    while len(current) > 1:
        round_idx += 1
        round_name = _round_name(len(current))
        print(f"\n=== {round_name} ({len(current)} players) ===")
        next_round: List[str] = []
        # 1 vs N, 2 vs N-1, ...
        pair_count = len(current) // 2
        for m_idx in range(pair_count):
            a = current[m_idx]
            b = current[-(m_idx + 1)]
            print_pairing_header(a, b, games_per_match)
            pts_a, pts_b, series_results = play_series(
                a,
                b,
                games_per_match,
                max_plies=max_plies,
                time_per_move=time_per_move,
                clock_initial=clock_initial,
                clock_increment=clock_increment,
                tiebreaks=tiebreaks,
                writer=writer,
            )
            winner: Optional[str]
            if pts_a > pts_b:
                winner = a
            elif pts_b > pts_a:
                winner = b
            else:
                # If still tied, pick higher seed (earlier in original list)
                idx_a = seeds.index(a)
                idx_b = seeds.index(b)
                winner = a if idx_a < idx_b else b
            next_round.append(winner)
            if writer is not None:
                writer.update_match(
                    round_name=round_name,
                    match_index=m_idx,
                    a=a,
                    b=b,
                    results=series_results,
                    pts_a=pts_a,
                    pts_b=pts_b,
                    winner=winner,
                )
        # Handle BYE for odd-sized rounds: the middle seed advances automatically
        if len(current) % 2 == 1:
            bye_seed = current[pair_count]
            print(f"BYE: {bye_seed} advances")
            next_round.append(bye_seed)
            if writer is not None:
                # Record a bye as a match with no opponent
                writer.update_match(
                    round_name=round_name,
                    match_index=pair_count,
                    a=bye_seed,
                    b=None,
                    results=[],
                    pts_a=0.0,
                    pts_b=0.0,
                    winner=bye_seed,
                )
        current = next_round

    champion = current[0]
    print(f"\n=== Champion: {champion} ===")
    if writer is not None:
        writer.write_se_summary(champion)
    return champion


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    all_known = set(get_agent_names())
    requested = [a.strip() for a in args.agents.split(",") if a.strip()]

    # Include/Exclude DynamicBot per flags
    if args.include_dynamic and "DynamicBot" not in requested:
        requested.append("DynamicBot")
    if args.exclude_dynamic:
        requested = [a for a in requested if a != "DynamicBot"]

    unknown = [a for a in requested if a not in all_known]
    if unknown:
        print("Невідомі агенти:", ", ".join(unknown))
        print("Доступні:", ", ".join(sorted(all_known)))
        return 2

    # Determine series length
    if args.games is not None:
        games_per_pair = int(args.games)
        if games_per_pair <= 0:
            print("--games має бути > 0")
            return 2
    else:
        if args.format:
            fmt_map = {"bo3": 3, "bo5": 5, "bo7": 7}
            games_per_pair = fmt_map[args.format]
        else:
            games_per_pair = int(args.bo)

    # Parse optional per-player clock like "1|0" (minutes|increment seconds)
    clock_initial: Optional[float] = None
    clock_increment: float = 0.0
    if args.clock:
        try:
            mins_str, inc_str = str(args.clock).split("|", 1)
            clock_initial = float(mins_str) * 60.0
            clock_increment = float(inc_str)
        except Exception:
            print("Невалідний формат --clock. Очікується M|inc, напр. 1|0")
            return 2

    print("Учасники:", ", ".join(requested))
    fmt_label = f"Bo{games_per_pair}" if games_per_pair % 2 == 1 else f"{games_per_pair} ігор"
    if clock_initial is not None:
        time_label = f"годинник: {int(clock_initial)}s + {clock_increment}s"
    else:
        time_label = f"{args.time}s" if args.time and args.time > 0 else "без ліміту"
    tb_label = "ON" if args.tiebreaks == "on" else "OFF"
    print(f"Формат: {fmt_label} | Без потоків | Макс. пліїв: {args.max_plies} | Ліміт на хід: {time_label} | Тай-брейки: {tb_label}")

    out_root = Path(ROOT) / args.out_root
    writer = TournamentOutputWriter(out_root=out_root, tag=args.tag)

    if args.mode == "rr":
        writer.set_round_robin_metadata(
            agents=requested,
            format_label=fmt_label,
            games_per_pair=games_per_pair,
            tiebreaks=(args.tiebreaks == "on"),
            max_plies=args.max_plies,
            time_per_move=(None if clock_initial is not None else (args.time if args.time and args.time > 0 else None)),
            clock_initial=clock_initial,
            clock_increment=clock_increment,
        )
        standings = run_round_robin(
            requested,
            games_per_pair,
            max_plies=args.max_plies,
            time_per_move=(None if clock_initial is not None else (args.time if args.time and args.time > 0 else None)),
            clock_initial=clock_initial,
            clock_increment=clock_increment,
            tiebreaks=(args.tiebreaks == "on"),
            writer=writer,
        )
        print("\nФінальна таблиця:")
        print_standings(standings)
        writer.write_summary(standings)
        return 0
    else:
        champion = run_single_elimination(
            requested,
            games_per_match=games_per_pair,
            max_plies=args.max_plies,
            time_per_move=(None if clock_initial is not None else (args.time if args.time and args.time > 0 else None)),
            clock_initial=clock_initial,
            clock_increment=clock_increment,
            tiebreaks=(args.tiebreaks == "on"),
            writer=writer,
        )
        print(f"Переможець турніру: {champion}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
