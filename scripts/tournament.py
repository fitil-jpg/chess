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
import itertools
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import math
from pathlib import Path
from datetime import datetime
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
        "--tiebreaks",
        type=str,
        choices=["on", "off"],
        default="on",
        help="Play a single deciding game if a series ends tied",
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
    print(f"Результат: {result} ({tag})")


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
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
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
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
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
    ) -> None:
        self.bracket["type"] = "round_robin"
        self.bracket["format"] = format_label
        self.bracket["agents"] = list(agents)
        self.bracket["games_per_pair"] = int(games_per_pair)
        self.bracket["tiebreaks"] = bool(tiebreaks)
        self.bracket["max_plies"] = int(max_plies)
        self.bracket["time_per_move"] = int(time_per_move) if time_per_move else None
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
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "pair": {"a": a, "b": b},
            "game_index": int(game_index),
            "white": white,
            "black": black,
            "result": result,
            "tiebreak": bool(tiebreak),
        }
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
        self.bracket["updated_at"] = datetime.utcnow().isoformat()
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
        seeds: List[str],
    ) -> None:
        self.bracket["type"] = "single_elimination"
        self.bracket["format"] = format_label
        self.bracket["agents"] = list(agents)
        self.bracket["tiebreaks"] = bool(tiebreaks)
        self.bracket["max_plies"] = int(max_plies)
        self.bracket["time_per_move"] = int(time_per_move) if time_per_move else None
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
    if not timeout_s or timeout_s <= 0:
        try:
            return agent.choose_move(board)
        except Exception:
            return None

    result = {"move": None}
    done = threading.Event()

    # Work on a lightweight copy to avoid any accidental cross-thread mutations.
    board_copy = board.copy(stack=False)

    def _worker():
        try:
            mv = agent.choose_move(board_copy)
            result["move"] = mv
        except Exception:
            result["move"] = None
        finally:
            done.set()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    done.wait(timeout=timeout_s)
    return result["move"] if done.is_set() else None


def play_single_game(
    white_agent_name: str,
    black_agent_name: str,
    *,
    max_plies: int,
    time_per_move: Optional[int] = None,
) -> str:
    """Play one game and return chess result string: '1-0', '0-1', or '1/2-1/2'.
    Technical loss is applied if an agent returns None or makes illegal move.
    """
    board = chess.Board()
    white_agent = make_agent(white_agent_name, chess.WHITE)
    black_agent = make_agent(black_agent_name, chess.BLACK)

    try:
        while not board.is_game_over() and len(board.move_stack) < max_plies:
            agent = white_agent if board.turn == chess.WHITE else black_agent
            move = _choose_move_with_timeout(agent, board, time_per_move)
            if move is None:
                # Immediate loss for side to move
                return "0-1" if board.turn == chess.WHITE else "1-0"
            try:
                board.push(move)
            except Exception:
                # Illegal move => technical loss for mover
                return "0-1" if board.turn == chess.WHITE else "1-0"
    except Exception:
        # Any unexpected exception from agent => their loss
        return "0-1" if board.turn == chess.WHITE else "1-0"

    if board.is_game_over():
        return board.result()
    # Safety draw if exceeded max plies
    return "1/2-1/2"


def play_series(
    a: str,
    b: str,
    series_games: int,
    *,
    max_plies: int,
    time_per_move: Optional[int] = None,
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

    for i in range(series_games):
        white, black = (a, b) if i % 2 == 0 else (b, a)
        print_game_header(i + 1, white, black)
        res = play_single_game(white, black, max_plies=max_plies, time_per_move=time_per_move)
        print_game_result(res)
        results.append(res)

        # Per-game log and live bracket update
        if writer is not None:
            writer.log_game(a=a, b=b, white=white, black=black, game_index=i + 1, result=res, tiebreak=False)

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

    # Optional single tiebreak game if the series ended tied on points
    if tiebreaks and abs(pts_a - pts_b) < 1e-9:
        tiebreak_idx = len(results)
        white, black = (a, b) if tiebreak_idx % 2 == 0 else (b, a)
        print_pairing_header(a, b, 1)
        print("Тай-брейк: 1 гра для визначення переможця")
        print_game_header(tiebreak_idx + 1, white, black)
        res = play_single_game(white, black, max_plies=max_plies, time_per_move=time_per_move)
        print_game_result(res)
        results.append(res)
        if writer is not None:
            writer.log_game(a=a, b=b, white=white, black=black, game_index=tiebreak_idx + 1, result=res, tiebreak=True)
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
            # If tiebreak still draws, leave points equal (overall tie persists)
            pts_a += 0.5
            pts_b += 0.5

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


def _seed_bracket_participants(agent_names: List[str]) -> List[str]:
    # For now, use the order provided as seed order
    return list(agent_names)


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

    print("Учасники:", ", ".join(requested))
    fmt_label = f"Bo{games_per_pair}" if games_per_pair % 2 == 1 else f"{games_per_pair} ігор"
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
            time_per_move=(args.time if args.time and args.time > 0 else None),
        )
        standings = run_round_robin(
            requested,
            games_per_pair,
            max_plies=args.max_plies,
            time_per_move=(args.time if args.time and args.time > 0 else None),
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
            time_per_move=(args.time if args.time and args.time > 0 else None),
            tiebreaks=(args.tiebreaks == "on"),
            writer=writer,
        )
        print(f"Переможець турніру: {champion}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
