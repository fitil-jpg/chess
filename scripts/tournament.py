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
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

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


class TournamentWriters:
    """Handles writing live bracket snapshots and per-game logs.

    Files:
      - output/tournaments/<timestamp>/bracket.json
      - output/tournaments/<timestamp>/match_logs.jsonl
    """

    def __init__(
        self,
        out_dir: Path,
        agent_names: List[str],
        games_per_pair: int,
        *,
        max_plies: int,
    ) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.bracket_path = self.out_dir / "bracket.json"
        self.logs_path = self.out_dir / "match_logs.jsonl"

        self.agent_names = list(agent_names)
        self.games_per_pair = int(games_per_pair)
        self.max_plies = int(max_plies)
        self.started_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

        # Initialize series map for all unique pairs
        self.series_map: Dict[str, Dict[str, object]] = {}
        for a, b in itertools.combinations(self.agent_names, 2):
            key = self._pair_key(a, b)
            self.series_map[key] = {
                "a": a,
                "b": b,
                "games_scheduled": self.games_per_pair,
                "games": [],  # list[{"white": str, "black": str, "result": str}]
                "points": {a: 0.0, b: 0.0},
            }

        # Write initial empty bracket
        self._write_bracket_snapshot()

    @staticmethod
    def _pair_key(a: str, b: str) -> str:
        x, y = sorted([a, b])
        return f"{x}__vs__{y}"

    def _compute_standings(self) -> Dict[str, Dict[str, object]]:
        # Reconstruct standings from recorded games
        standings: Dict[str, PlayerStats] = {name: PlayerStats(name) for name in self.agent_names}
        for series in self.series_map.values():
            games = series["games"]  # type: ignore[assignment]
            for g in games:  # type: ignore[assignment]
                white = g["white"]
                black = g["black"]
                result = g["result"]
                standings[white].record(result, as_white=True)
                standings[black].record(result, as_white=False)

        return {
            name: {
                "played": s.played,
                "wins": s.wins,
                "draws": s.draws,
                "losses": s.losses,
                "points": s.points,
            }
            for name, s in standings.items()
        }

    def _write_bracket_snapshot(self) -> None:
        total_pairs = len(self.series_map)
        completed_games = sum(len(series["games"]) for series in self.series_map.values())
        total_games = total_pairs * self.games_per_pair

        bracket = {
            "tournament": {
                "type": "round_robin",
                "agents": self.agent_names,
                "games_per_pair": self.games_per_pair,
                "max_plies": self.max_plies,
                "started_at": self.started_at,
            },
            "series": [
                {
                    "a": series["a"],
                    "b": series["b"],
                    "games_scheduled": series["games_scheduled"],
                    "results": [g["result"] for g in series["games"]],
                    "points": series["points"],
                }
                for series in self.series_map.values()
            ],
            "standings": self._compute_standings(),
            "progress": {
                "completed_games": completed_games,
                "total_games": total_games,
            },
        }
        self.bracket_path.write_text(json.dumps(bracket, ensure_ascii=False, indent=2), encoding="utf-8")

    def record_game(
        self,
        a: str,
        b: str,
        game_index: int,
        white: str,
        black: str,
        result: str,
    ) -> None:
        # Update series state
        key = self._pair_key(a, b)
        series = self.series_map[key]
        series_games: List[Dict[str, str]] = series["games"]  # type: ignore[assignment]
        series_games.append({"white": white, "black": black, "result": result})

        points: Dict[str, float] = series["points"]  # type: ignore[assignment]
        if result == "1-0":
            points[white] = points.get(white, 0.0) + 1.0
        elif result == "0-1":
            points[black] = points.get(black, 0.0) + 1.0
        else:
            points[a] = points.get(a, 0.0) + 0.5
            points[b] = points.get(b, 0.0) + 0.5

        # Append per-game log line
        event = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "pair": {"a": a, "b": b},
            "game_index": game_index,
            "white": white,
            "black": black,
            "result": result,
            "series_points": {a: points.get(a, 0.0), b: points.get(b, 0.0)},
        }
        with open(self.logs_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Write updated bracket snapshot
        self._write_bracket_snapshot()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sequential round-robin tournament runner")
    parser.add_argument(
        "--agents",
        type=str,
        default="DynamicBot,FortifyBot,AggressiveBot,EndgameBot,KingValueBot,RandomBot",
        help="Comma-separated list of agent names (see chess_ai.bot_agent.get_agent_names)",
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
        "--max-plies",
        type=int,
        default=600,
        help="Safety cap: maximum plies per game (to avoid infinite games)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Optional output directory. Default: output/tournaments/<timestamp>",
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


def play_single_game(white_agent_name: str, black_agent_name: str, *, max_plies: int) -> str:
    """Play one game and return chess result string: '1-0', '0-1', or '1/2-1/2'.
    Technical loss is applied if an agent returns None or makes illegal move.
    """
    board = chess.Board()
    white_agent = make_agent(white_agent_name, chess.WHITE)
    black_agent = make_agent(black_agent_name, chess.BLACK)

    try:
        while not board.is_game_over() and len(board.move_stack) < max_plies:
            agent = white_agent if board.turn == chess.WHITE else black_agent
            move = agent.choose_move(board)
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
    standings: Optional[Dict[str, PlayerStats]] = None,
    writers: Optional[TournamentWriters] = None,
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
        res = play_single_game(white, black, max_plies=max_plies)
        print_game_result(res)
        results.append(res)

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

        # Live standings update and write logs if configured
        if standings is not None:
            standings[a].record(res, as_white=(white == a))
            standings[b].record(res, as_white=(white == b))
            print_standings(standings)

        if writers is not None:
            writers.record_game(a, b, i + 1, white, black, res)

        # Best-of early stop
        if needed is not None and (pts_a >= needed or pts_b >= needed):
            break

    return pts_a, pts_b, results


def run_round_robin(
    agent_names: List[str],
    games_per_pair: int,
    *,
    max_plies: int,
    writers: Optional[TournamentWriters] = None,
) -> Dict[str, PlayerStats]:
    standings: Dict[str, PlayerStats] = {name: PlayerStats(name) for name in agent_names}

    pairs = list(itertools.combinations(agent_names, 2))
    for a, b in pairs:
        print_pairing_header(a, b, games_per_pair)
        _pts_a, _pts_b, _series_results = play_series(
            a,
            b,
            games_per_pair,
            max_plies=max_plies,
            standings=standings,
            writers=writers,
        )

    return standings


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    all_known = set(get_agent_names())
    requested = [a.strip() for a in args.agents.split(",") if a.strip()]

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
        games_per_pair = int(args.bo)

    print("Учасники:", ", ".join(requested))
    print(f"Формат: {'Bo'+str(games_per_pair) if games_per_pair % 2 == 1 else str(games_per_pair)+' ігор'} | Без потоків | Макс. пліїв: {args.max_plies}")

    # Prepare timestamped output directory
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path(ROOT) / "output" / "tournaments" / ts

    writers = TournamentWriters(out_dir, requested, games_per_pair, max_plies=args.max_plies)

    standings = run_round_robin(
        requested,
        games_per_pair,
        max_plies=args.max_plies,
        writers=writers,
    )

    print("\nФінальна таблиця:")
    print_standings(standings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
