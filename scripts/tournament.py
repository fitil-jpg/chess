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
import time
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


def _play_timed_game(
    white_agent_name: str,
    black_agent_name: str,
    *,
    max_plies: int,
    white_seconds: float,
    black_seconds: float,
    increment: float = 0.0,
    armageddon_black_draw_odds: bool = False,
) -> tuple[str, float, float]:
    """Play one game with simple headless clocks.

    Returns (result, white_time_left, black_time_left).

    Time model:
    - The time spent inside choose_move is subtracted from the mover's clock.
    - If the mover's clock reaches 0 or below after their think, they lose on time
      before the move is applied.
    - No increment by default; can be configured.

    Armageddon:
    - If armageddon_black_draw_odds is True and the final position is a draw,
      the result is converted to a Black win ("0-1").
    """
    board = chess.Board()
    white_agent = make_agent(white_agent_name, chess.WHITE)
    black_agent = make_agent(black_agent_name, chess.BLACK)

    w_time = float(white_seconds)
    b_time = float(black_seconds)

    try:
        while not board.is_game_over() and len(board.move_stack) < max_plies:
            mover_is_white = (board.turn == chess.WHITE)
            agent = white_agent if mover_is_white else black_agent

            start = time.monotonic()
            try:
                ret = agent.choose_move(board)
            except TypeError:
                ret = agent.choose_move(board, debug=True)
            except Exception:
                # Unexpected agent error ⇒ immediate loss for side to move
                return ("0-1" if mover_is_white else "1-0", w_time, b_time)
            elapsed = time.monotonic() - start

            # Deduct thinking time
            if mover_is_white:
                w_time -= elapsed
                if w_time <= 0.0:
                    return ("0-1", 0.0, max(0.0, b_time))
            else:
                b_time -= elapsed
                if b_time <= 0.0:
                    return ("1-0", max(0.0, w_time), 0.0)

            # Extract move
            move = ret[0] if isinstance(ret, tuple) else ret
            if move is None:
                # Technical loss for the mover
                return ("0-1" if mover_is_white else "1-0", w_time, b_time)
            try:
                board.push(move)
            except Exception:
                # Illegal move ⇒ technical loss for the mover
                return ("0-1" if mover_is_white else "1-0", w_time, b_time)

            # Apply increment after a successful move
            if increment:
                if mover_is_white:
                    w_time += increment
                else:
                    b_time += increment
    except Exception:
        # Any unexpected exception from agent loop ⇒ mover loses
        return ("0-1" if board.turn == chess.WHITE else "1-0", w_time, b_time)

    # Game ended normally or by ply cap
    if board.is_game_over():
        try:
            res = board.result(claim_draw=True)
        except TypeError:
            res = board.result()
    else:
        res = "1/2-1/2"

    if armageddon_black_draw_odds and res == "1/2-1/2":
        res = "0-1"
    return res, max(0.0, w_time), max(0.0, b_time)


def play_series(a: str, b: str, series_games: int, *, max_plies: int) -> Tuple[float, float, List[str]]:
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

        # Best-of early stop
        if needed is not None and (pts_a >= needed or pts_b >= needed):
            break

    return pts_a, pts_b, results


def play_series_with_tiebreaks(
    a: str,
    b: str,
    series_games: int,
    *,
    max_plies: int,
) -> Tuple[float, float, List[str]]:
    """Play a series and, if tied, apply tie-breaks:
    - Two blitz games (1|0) with alternating colors
    - If still tied, Armageddon: White 60s vs Black 45s, draw → Black
    Returns (points_a, points_b, results_in_order) including tie-break games.
    """
    pts_a, pts_b, results = play_series(a, b, series_games, max_plies=max_plies)

    # If the scheduled series is tied, go to tie-breaks
    if abs(pts_a - pts_b) < 1e-9:
        # Blitz tie-breaks: two games 1|0, alternating colors
        print("Тай-брейки: дві бліц-партії 1|0 (без інкременту)")
        for j in range(2):
            i = len(results)
            white, black = (a, b) if (i % 2 == 0) else (b, a)
            print_game_header(i + 1, white, black)
            res, w_left, b_left = _play_timed_game(
                white,
                black,
                max_plies=max_plies,
                white_seconds=60.0,
                black_seconds=60.0,
                increment=0.0,
                armageddon_black_draw_odds=False,
            )
            print_game_result(res)
            print(f"T: W {w_left:.1f}s / B {b_left:.1f}s")
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

        # If still tied, Armageddon
        if abs(pts_a - pts_b) < 1e-9:
            i = len(results)
            white, black = (a, b) if (i % 2 == 0) else (b, a)
            print("Армагеддон: Білі 60с vs Чорні 45с (нічия → перемога чорних)")
            print_game_header(i + 1, white, black)
            res, w_left, b_left = _play_timed_game(
                white,
                black,
                max_plies=max_plies,
                white_seconds=60.0,
                black_seconds=45.0,
                increment=0.0,
                armageddon_black_draw_odds=True,
            )
            print_game_result(res)
            print(f"T: W {w_left:.1f}s / B {b_left:.1f}s")
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

    return pts_a, pts_b, results


def run_round_robin(agent_names: List[str], games_per_pair: int, *, max_plies: int) -> Dict[str, PlayerStats]:
    standings: Dict[str, PlayerStats] = {name: PlayerStats(name) for name in agent_names}

    pairs = list(itertools.combinations(agent_names, 2))
    for a, b in pairs:
        print_pairing_header(a, b, games_per_pair)
        pts_a, pts_b, series_results = play_series_with_tiebreaks(a, b, games_per_pair, max_plies=max_plies)

        # Per-game standings update with correct colors
        for i, res in enumerate(series_results):
            white, black = (a, b) if i % 2 == 0 else (b, a)
            standings[a].record(res, as_white=(white == a))
            standings[b].record(res, as_white=(white == b))
            print_standings(standings)

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

    standings = run_round_robin(requested, games_per_pair, max_plies=args.max_plies)

    print("\nФінальна таблиця:")
    print_standings(standings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
