#!/usr/bin/env python3
"""
Headless tournament runner (no threading):

- Single-elimination bracket with Bo3/Bo5/Bo7 series (default)
- Round-robin mode preserved behind --round-robin flag
- Per-move time control (default 60s per player, 1|0)
- Tie-breaks for bracket: two extra games (same time control), then Armageddon (White 60s vs Black 45s, draw → Black)

Examples:
  # Bracket (default mode)
  python scripts/tournament.py \
    --agents DynamicBot,NeuralBot,FortifyBot,AggressiveBot,EndgameBot,CriticalBot,KingValueBot,TrapBot \
    --bo 5 --time 60

  # Round-robin (legacy)
  python scripts/tournament.py --agents DynamicBot,FortifyBot,AggressiveBot --bo 3 --round-robin

Notes:
- Scoring: win=1.0, draw=0.5, loss=0.0
- Colors alternate by game within a series; for odd BoN, higher seed is White in G1 and the last game if needed
- Technical loss on illegal move/agent error/returned None or on time expiration
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import time
import json
from datetime import datetime
import math
import signal
import contextlib

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


# ----------------------------- Utilities (SAN, timing) -----------------------------

def _moves_san_string(board: chess.Board) -> str:
    """Build SAN for the entire game from the move stack."""
    temp = chess.Board()
    parts: List[str] = []
    for mv in board.move_stack:
        parts.append(temp.san(mv))
        temp.push(mv)
    out: List[str] = []
    for i, san in enumerate(parts, start=1):
        if i % 2 == 1:
            move_no = (i + 1) // 2
            out.append(f"{move_no}. {san}")
        else:
            out.append(san)
    return " ".join(out)


@contextlib.contextmanager
def _time_limit(seconds: float):
    """Context manager to enforce a wall-clock time limit using SIGALRM.

    Raises TimeoutError if exceeded. Only works on Unix; if signals fail,
    falls back to no preemption (the caller should check elapsed time).
    """
    seconds = max(0.0, float(seconds))
    use_signal = hasattr(signal, "setitimer") and seconds > 0
    if not use_signal:
        yield
        return
    old_handler = signal.getsignal(signal.SIGALRM)
    def _handler(_signum, _frame):
        raise TimeoutError("move timed out")
    try:
        signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        yield
    finally:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
        except Exception:
            pass
        try:
            signal.signal(signal.SIGALRM, old_handler)
        except Exception:
            pass


# ----------------------------- Bracket types -----------------------------

@dataclass
class GameLog:
    round_label: str
    match_id: str
    game_index: int
    white: str
    black: str
    result: str
    reason: str
    white_time_left: float
    black_time_left: float
    san: str


@dataclass
class MatchRecord:
    id: str
    seed_a: int
    seed_b: int
    name_a: Optional[str]
    name_b: Optional[str]
    format: str
    scheduled_games: int
    results: List[str] = field(default_factory=list)
    points_a: float = 0.0
    points_b: float = 0.0
    tiebreak: Dict[str, Any] = field(default_factory=dict)  # {"extra": [...], "armageddon": "1-0"}
    winner_seed: Optional[int] = None
    winner_name: Optional[str] = None


@dataclass
class RoundRecord:
    name: str
    matches: List[MatchRecord]


# ----------------------------- Core game runners -----------------------------

def _push_or_illegal(board: chess.Board, move: chess.Move) -> bool:
    try:
        board.push(move)
        return True
    except Exception:
        return False


def play_single_game_timed(
    white_agent_name: str,
    black_agent_name: str,
    *,
    time_white_s: float,
    time_black_s: float,
    max_plies: int,
) -> Tuple[str, str, float, float, str]:
    """Play one timed game; return (result, reason, white_time_left, black_time_left, san)."""
    board = chess.Board()
    white_agent = make_agent(white_agent_name, chess.WHITE)
    black_agent = make_agent(black_agent_name, chess.BLACK)

    remain_white = float(time_white_s)
    remain_black = float(time_black_s)

    result: Optional[str] = None
    reason: str = ""

    while not board.is_game_over() and len(board.move_stack) < max_plies:
        side = chess.WHITE if board.turn == chess.WHITE else chess.BLACK
        agent = white_agent if side == chess.WHITE else black_agent
        time_left = remain_white if side == chess.WHITE else remain_black

        start = time.monotonic()
        move = None
        timed_out = False
        error_occured = False
        try:
            with _time_limit(time_left + 1e-3):
                move = agent.choose_move(board)
        except TimeoutError:
            timed_out = True
        except Exception:
            error_occured = True
        elapsed = time.monotonic() - start

        if side == chess.WHITE:
            remain_white -= elapsed
        else:
            remain_black -= elapsed

        # Time loss
        if timed_out or (side == chess.WHITE and remain_white <= 0.0) or (side == chess.BLACK and remain_black <= 0.0):
            result = "0-1" if side == chess.WHITE else "1-0"
            reason = "time"
            break

        if error_occured:
            result = "0-1" if side == chess.WHITE else "1-0"
            reason = "error"
            break

        if move is None:
            result = "0-1" if side == chess.WHITE else "1-0"
            reason = "no_move"
            break

        if not _push_or_illegal(board, move):
            result = "0-1" if side == chess.WHITE else "1-0"
            reason = "illegal"
            break

    if result is None:
        if board.is_game_over():
            outcome = board.outcome()
            result = board.result()
            if outcome is not None:
                reason = str(outcome.termination)
            else:
                reason = "game_over"
        else:
            result = "1/2-1/2"
            reason = "max_plies"

    san = _moves_san_string(board)
    return result, reason, max(0.0, remain_white), max(0.0, remain_black), san


def play_series_timed(
    a: str,
    b: str,
    series_games: int,
    *,
    max_plies: int,
    base_time_s: float,
    first_white: str,
    round_label: str,
    match_id: str,
    game_logs_out: List[GameLog],
) -> Tuple[float, float, List[str]]:
    """Play timed series with alternating colors. Returns (points_a, points_b, results)."""
    results: List[str] = []
    pts_a = 0.0
    pts_b = 0.0
    needed = (series_games // 2) + 1 if series_games % 2 == 1 else None

    for i in range(series_games):
        # Determine colors: alternate from first_white
        if i % 2 == 0:
            white, black = first_white, (b if first_white == a else a)
        else:
            white, black = ((b if first_white == a else a), first_white)

        res, why, tw, tb, san = play_single_game_timed(
            white, black,
            time_white_s=base_time_s,
            time_black_s=base_time_s,
            max_plies=max_plies,
        )
        results.append(res)
        game_logs_out.append(
            GameLog(
                round_label=round_label,
                match_id=match_id,
                game_index=len(results),
                white=white,
                black=black,
                result=res,
                reason=why,
                white_time_left=tw,
                black_time_left=tb,
                san=san,
            )
        )

        # Update points relative to a/b mapping
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

        if needed is not None and (pts_a >= needed or pts_b >= needed):
            break

        # Flip first_white for next iteration only affects alternation when i even/odd; we handle by formula above

    return pts_a, pts_b, results


# ----------------------------- Round-robin (legacy) -----------------------------


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
    parser = argparse.ArgumentParser(description="Headless tournament runner (bracket default; round-robin via flag)")
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
        "--time",
        type=int,
        default=60,
        help="Per-player time in seconds for main and tie-break games (Armageddon is fixed 60/45)",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=600,
        help="Safety cap: maximum plies per game (to avoid infinite games)",
    )
    parser.add_argument(
        "--round-robin",
        action="store_true",
        help="Run legacy round-robin instead of single-elimination bracket",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for outputs; default is output/tournaments/<timestamp>",
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


def run_round_robin(agent_names: List[str], games_per_pair: int, *, max_plies: int) -> Dict[str, PlayerStats]:
    standings: Dict[str, PlayerStats] = {name: PlayerStats(name) for name in agent_names}

    pairs = list(itertools.combinations(agent_names, 2))
    for a, b in pairs:
        print_pairing_header(a, b, games_per_pair)
        pts_a, pts_b, series_results = play_series(a, b, games_per_pair, max_plies=max_plies)

        # Per-game standings update with correct colors
        for i, res in enumerate(series_results):
            white, black = (a, b) if i % 2 == 0 else (b, a)
            standings[a].record(res, as_white=(white == a))
            standings[b].record(res, as_white=(white == b))
            print_standings(standings)

    return standings


# ----------------------------- Bracket helpers -----------------------------

def _next_power_of_two(n: int) -> int:
    p = 1
    while p < n:
        p <<= 1
    return p


def _initial_pairs(num_slots: int) -> List[Tuple[int, int]]:
    """Return seed position pairs for the first round: (1,num_slots), (2,num_slots-1), ..."""
    pairs: List[Tuple[int, int]] = []
    left = 1
    right = num_slots
    while left < right:
        pairs.append((left, right))
        left += 1
        right -= 1
    return pairs


def _round_name(size: int) -> str:
    if size == 2:
        return "Final"
    if size == 4:
        return "Semifinals"
    if size == 8:
        return "Quarterfinals"
    if size == 16:
        return "Round of 16"
    return f"Round of {size}"


def _series_label(bo: int) -> str:
    return f"Bo{bo}" if bo % 2 == 1 else f"{bo} games"


def run_single_elimination(
    agents: List[str],
    *,
    games_per_match: int,
    base_time_s: int,
    max_plies: int,
    output_dir: Optional[str] = None,
) -> Tuple[List[RoundRecord], List[GameLog]]:
    # Seeding: agents order as given (1..n)
    n = len(agents)
    m = _next_power_of_two(n)
    # Map seed -> name or None for byes
    seeds: Dict[int, Optional[str]] = {}
    for i in range(1, m + 1):
        if i <= n:
            seeds[i] = agents[i - 1]
        else:
            seeds[i] = None

    rounds: List[RoundRecord] = []
    game_logs: List[GameLog] = []

    # Prepare output dir
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = output_dir or os.path.join("output", "tournaments", ts)
    os.makedirs(out_dir, exist_ok=True)

    current_size = m
    current_seeds = seeds.copy()
    round_index = 0

    while current_size >= 2:
        round_index += 1
        round_label = _round_name(current_size)
        pairs = _initial_pairs(current_size)
        match_records: List[MatchRecord] = []
        winners: Dict[int, Optional[str]] = {}
        # Build mapping from pair index to next round seed position
        # Winners from (i,j) go to new positions: preserve bracket order [left-first winners, right-side winners]
        next_seed_pos = 1
        for idx, (sa, sb) in enumerate(pairs, start=1):
            name_a = current_seeds.get(sa)
            name_b = current_seeds.get(sb)
            match_id = f"{round_label.replace(' ', '')}{idx}"
            rec = MatchRecord(
                id=match_id,
                seed_a=sa,
                seed_b=sb,
                name_a=name_a,
                name_b=name_b,
                format=_series_label(games_per_match),
                scheduled_games=games_per_match,
            )

            # Handle byes
            if name_a is None and name_b is None:
                # No one advances (should not happen in normal brackets)
                winners[next_seed_pos] = None
                match_records.append(rec)
                next_seed_pos += 1
                continue
            if name_a is None:
                rec.winner_seed = sb
                rec.winner_name = name_b
                winners[next_seed_pos] = name_b
                match_records.append(rec)
                next_seed_pos += 1
                continue
            if name_b is None:
                rec.winner_seed = sa
                rec.winner_name = name_a
                winners[next_seed_pos] = name_a
                match_records.append(rec)
                next_seed_pos += 1
                continue

            # Play series: higher seed (smaller number) has White in G1 if odd Bo
            higher_seed_name = name_a if sa < sb else name_b
            pts_a, pts_b, reslist = play_series_timed(
                name_a,
                name_b,
                games_per_match,
                max_plies=max_plies,
                base_time_s=base_time_s,
                first_white=higher_seed_name,
                round_label=round_label,
                match_id=match_id,
                game_logs_out=game_logs,
            )
            rec.results = reslist
            rec.points_a = pts_a
            rec.points_b = pts_b

            # Decide winner or tie-break
            if pts_a != pts_b:
                if pts_a > pts_b:
                    rec.winner_seed = sa
                    rec.winner_name = name_a
                    winners[next_seed_pos] = name_a
                else:
                    rec.winner_seed = sb
                    rec.winner_name = name_b
                    winners[next_seed_pos] = name_b
                match_records.append(rec)
                next_seed_pos += 1
                continue

            # Tie-break: two extra games at same control (alternate colors continuing the sequence)
            extra: List[str] = []
            # Continue color alternation: next game index is len(reslist)
            next_index = len(reslist)
            # Compute white for next game based on alternation from first_white
            def _color_for_index(i: int) -> Tuple[str, str]:
                if i % 2 == 0:
                    return higher_seed_name, (name_b if higher_seed_name == name_a else name_a)
                else:
                    return ((name_b if higher_seed_name == name_a else name_a), higher_seed_name)

            tb_pts_a = 0.0
            tb_pts_b = 0.0
            for j in range(2):
                white, black = _color_for_index(next_index + j)
                res, why, tw, tb, san = play_single_game_timed(
                    white, black,
                    time_white_s=60.0,
                    time_black_s=60.0,
                    max_plies=max_plies,
                )
                extra.append(res)
                game_logs.append(
                    GameLog(
                        round_label=round_label,
                        match_id=match_id,
                        game_index=len(reslist) + j + 1,
                        white=white,
                        black=black,
                        result=res,
                        reason=why,
                        white_time_left=tw,
                        black_time_left=tb,
                        san=san,
                    )
                )
                if res == "1-0":
                    if white == name_a:
                        tb_pts_a += 1.0
                    else:
                        tb_pts_b += 1.0
                elif res == "0-1":
                    if white == name_a:
                        tb_pts_b += 1.0
                    else:
                        tb_pts_a += 1.0
                else:
                    tb_pts_a += 0.5
                    tb_pts_b += 0.5

            rec.tiebreak["extra"] = extra
            pts_a += tb_pts_a
            pts_b += tb_pts_b

            if pts_a != pts_b:
                if pts_a > pts_b:
                    rec.winner_seed = sa
                    rec.winner_name = name_a
                    winners[next_seed_pos] = name_a
                else:
                    rec.winner_seed = sb
                    rec.winner_name = name_b
                    winners[next_seed_pos] = name_b
                match_records.append(rec)
                next_seed_pos += 1
                continue

            # Armageddon: color continues alternation; White 60s, Black 45s; draw => Black advances
            white_arm, black_arm = _color_for_index(next_index + 2)
            res, why, tw, tb, san = play_single_game_timed(
                white_arm, black_arm,
                time_white_s=60.0,
                time_black_s=45.0,
                max_plies=max_plies,
            )
            game_logs.append(
                GameLog(
                    round_label=round_label,
                    match_id=match_id,
                    game_index=len(reslist) + 3,
                    white=white_arm,
                    black=black_arm,
                    result=res,
                    reason=f"armageddon:{why}",
                    white_time_left=tw,
                    black_time_left=tb,
                    san=san,
                )
            )
            rec.tiebreak["armageddon"] = res

            # Determine winner with Armageddon rule
            if res == "1/2-1/2":
                # Draw => Black wins
                winner_name = black_arm
            elif res == "1-0":
                winner_name = white_arm
            else:
                winner_name = black_arm

            if winner_name == name_a:
                rec.winner_seed = sa
                rec.winner_name = name_a
                winners[next_seed_pos] = name_a
            else:
                rec.winner_seed = sb
                rec.winner_name = name_b
                winners[next_seed_pos] = name_b

            match_records.append(rec)
            next_seed_pos += 1

        # Persist round record
        rounds.append(RoundRecord(name=round_label, matches=match_records))

        # Build seeds for next round
        current_seeds = {i: winners.get(i) for i in range(1, (current_size // 2) + 1)}
        # Re-seed positions 1..current_size//2 with winners in order
        current_size //= 2
        # Expand seed positions to 1..current_size (we already used condensed positions)
        # Here, we simply map compact positions 1..k to actual bracket positions 1..k for next iteration

    # Output artifacts
    bracket_json = {
        "timestamp": ts,
        "agents": agents,
        "format": _series_label(games_per_match),
        "time_seconds": base_time_s,
        "rounds": [
            {
                "name": r.name,
                "matches": [
                    {
                        "id": m.id,
                        "seed_a": m.seed_a,
                        "seed_b": m.seed_b,
                        "name_a": m.name_a,
                        "name_b": m.name_b,
                        "format": m.format,
                        "scheduled_games": m.scheduled_games,
                        "results": m.results,
                        "points_a": m.points_a,
                        "points_b": m.points_b,
                        "tiebreak": m.tiebreak,
                        "winner_seed": m.winner_seed,
                        "winner_name": m.winner_name,
                    }
                    for m in r.matches
                ],
            }
            for r in rounds
        ],
    }
    with open(os.path.join(out_dir, "bracket.json"), "w", encoding="utf-8") as f:
        json.dump(bracket_json, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, "match_logs.jsonl"), "w", encoding="utf-8") as f:
        for gl in game_logs:
            f.write(
                json.dumps(
                    {
                        "round": gl.round_label,
                        "match": gl.match_id,
                        "game": gl.game_index,
                        "white": gl.white,
                        "black": gl.black,
                        "result": gl.result,
                        "reason": gl.reason,
                        "white_time_left": round(gl.white_time_left, 3),
                        "black_time_left": round(gl.black_time_left, 3),
                        "san": gl.san,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    # Summary
    def _champion_name() -> str:
        # Champion is the last winner recorded
        for r in reversed(rounds):
            for m in r.matches:
                if m.winner_name:
                    return m.winner_name
        return ""

    with open(os.path.join(out_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(f"Format: {_series_label(games_per_match)} | Time: {base_time_s}s | Players: {len(agents)}\n")
        for r in rounds:
            f.write(f"\n{r.name}\n")
            for m in r.matches:
                res_text = f"{sum(1 for x in m.results if x=='1-0') + sum(1 for x in m.tiebreak.get('extra', []) if x=='1-0')}–{sum(1 for x in m.results if x=='0-1') + sum(1 for x in m.tiebreak.get('extra', []) if x=='0-1')}"
                f.write(
                    f"{m.id:<6} {m.name_a or '—'} vs {m.name_b or '—'} | {m.format} | Winner: {m.winner_name or '—'}\n"
                )
        champ = _champion_name()
        if champ:
            f.write(f"\nChampion: {champ}\n")

    return rounds, game_logs


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

    if args.round_robin:
        print("Учасники:", ", ".join(requested))
        print(
            f"Формат: {'Bo'+str(games_per_pair) if games_per_pair % 2 == 1 else str(games_per_pair)+' ігор'} | Без потоків | Макс. пліїв: {args.max_plies}"
        )
        standings = run_round_robin(requested, games_per_pair, max_plies=args.max_plies)
        print("\nФінальна таблиця:")
        print_standings(standings)
        return 0

    # Bracket mode
    print("Учасники:", ", ".join(requested))
    print(
        f"Формат: {'Bo'+str(games_per_pair) if games_per_pair % 2 == 1 else str(games_per_pair)+' ігор'} | Час: {args.time}s | Без потоків | Макс. пліїв: {args.max_plies}"
    )
    rounds, _logs = run_single_elimination(
        requested,
        games_per_match=games_per_pair,
        base_time_s=int(args.time),
        max_plies=args.max_plies,
        output_dir=args.output_dir,
    )

    # Print console summary of bracket
    print("\nБРАКЕТ:")
    for r in rounds:
        print(f"\n{r.name}")
        for m in r.matches:
            print(
                f"{m.id:<6} {m.name_a or '—'} vs {m.name_b or '—'} | {m.format} | Winner: {m.winner_name or '—'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
