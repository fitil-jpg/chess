#!/usr/bin/env python3
"""Command-line helper to inspect recorded engine runs."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Sequence

import chess

from chess_ai.threat_map import ThreatMap
from main import annotated_board
from utils.load_runs import load_runs
from utils.metrics_sidebar import build_sidebar_metrics


_THREAT_MAPS: dict[chess.Color, ThreatMap] = {}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description="Replay a recorded run and print annotated boards in the terminal.",
    )
    parser.add_argument(
        "--runs",
        default="runs",
        help="Directory that stores run JSON files (default: %(default)s).",
    )
    parser.add_argument(
        "--game-id",
        help="Identifier of the run to replay (matches the JSON filename without extension).",
    )
    parser.add_argument(
        "--index",
        type=int,
        help="Zero-based index of the run to replay when several files are available.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Print the entire sequence without stopping for input.",
    )
    parser.add_argument(
        "--unicode",
        action="store_true",
        help="Render boards using Unicode figurines instead of ASCII.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of moves to display (defaults to the full game).",
    )
    return parser.parse_args(argv)


def _normalise_fen(value: str) -> str:
    value = value.strip()
    if value.lower() == "startpos":
        return chess.STARTING_FEN
    return value


def _select_run(
    runs: Sequence[dict], *, game_id: str | None, index: int | None
) -> dict | None:
    if not runs:
        return None

    if game_id is not None:
        for run in runs:
            if run.get("game_id") == game_id:
                return run
        print(f"No run with game_id '{game_id}' was found.", file=sys.stderr)
        return None

    if index is not None:
        if index < 0 or index >= len(runs):
            print(
                f"Run index {index} is out of range. Available indices: 0..{len(runs) - 1}",
                file=sys.stderr,
            )
            return None
        return runs[index]

    if len(runs) == 1:
        return runs[0]

    print("Multiple runs are available; please specify --game-id or --index.", file=sys.stderr)
    for idx, run in enumerate(runs):
        gid = run.get("game_id", "<unknown>")
        result = run.get("result", "*")
        move_count = len(run.get("moves", ()))
        print(f"  [{idx}] {gid}  (result: {result}, moves: {move_count})", file=sys.stderr)
    return None


def _apply_move(board: chess.Board, move_text: str) -> bool:
    """Apply *move_text* to *board*, accepting SAN or UCI notation."""

    move_text = move_text.strip()
    if not move_text:
        return False

    try:
        board.push_san(move_text)
        return True
    except ValueError:
        try:
            move = chess.Move.from_uci(move_text)
        except ValueError:
            return False
        if not board.is_legal(move):
            return False
        board.push(move)
        return True


def _module_info(
    modules_w: Sequence[str], modules_b: Sequence[str], move_index: int
) -> Iterable[str]:
    """Yield descriptive strings for module usage at *move_index*."""

    white_idx = (move_index + 2) // 2 - 1
    if white_idx >= 0:
        if white_idx < len(modules_w):
            yield f"White module #{white_idx + 1}: {modules_w[white_idx]}"
        else:
            yield f"White module #{white_idx + 1}: <missing>"

    black_idx = (move_index + 1) // 2 - 1
    if black_idx >= 0:
        if black_idx < len(modules_b):
            yield f"Black module #{black_idx + 1}: {modules_b[black_idx]}"
        else:
            yield f"Black module #{black_idx + 1}: <missing>"


def _display_position(
    run: dict,
    board: chess.Board,
    position_index: int,
    *,
    unicode: bool,
    move_text: str | None,
    modules_w: Sequence[str],
    modules_b: Sequence[str],
) -> None:
    """Print the board with contextual info for *position_index*."""

    game_id = run.get("game_id", "<unknown>")
    result = run.get("result", "*")

    info_lines: list[str] = [f"Game: {game_id}", f"Result: {result}"]

    if position_index == 0:
        info_lines.append("Initial position")
    else:
        assert move_text is not None
        move_index = position_index - 1
        side = "White" if move_index_is_white(move_index) else "Black"
        move_number = move_index // 2 + 1
        info_lines.append(f"Move {move_number} ({side}): {move_text}")
        info_lines.extend(_module_info(modules_w, modules_b, move_index))

    info_lines.append(f"To move: {'White' if board.turn == chess.WHITE else 'Black'}")
    info_lines.append(f"FEN: {board.fen()}")
    info_lines.extend(build_sidebar_metrics(board, _THREAT_MAPS))

    diagram = annotated_board(board, info_lines, unicode=unicode, side_by_side=True)
    print(diagram)


def move_index_is_white(move_index: int) -> bool:
    """Return ``True`` if *move_index* corresponds to a White move."""

    return move_index % 2 == 0


def replay_run(run: dict, *, unicode: bool, step: bool, limit: int | None) -> None:
    moves: Sequence[str] = run.get("moves", [])
    fens: Sequence[str] = run.get("fens", [])
    modules_w: Sequence[str] = run.get("modules_w", [])
    modules_b: Sequence[str] = run.get("modules_b", [])

    if not fens:
        fens = [chess.STARTING_FEN]

    try:
        start_board = chess.Board(_normalise_fen(fens[0]))
    except ValueError as exc:
        raise SystemExit(f"Invalid starting FEN: {exc}") from exc

    total_moves = len(moves)
    if limit is not None:
        if limit < 0:
            limit = 0
        total_moves = min(total_moves, limit)

    positions_to_show = max(1, total_moves + 1)

    progression = start_board.copy(stack=False)

    print(
        f"Replaying {run.get('game_id', '<unknown>')} – {len(moves)} moves, result {run.get('result', '*')}."
    )

    for position_index in range(positions_to_show):
        if position_index < len(fens):
            fen_text = _normalise_fen(fens[position_index])
            try:
                board_to_show = chess.Board(fen_text)
            except ValueError as exc:
                print(
                    f"Warning: invalid FEN at index {position_index}: {exc}. Using reconstructed position instead.",
                    file=sys.stderr,
                )
                board_to_show = progression.copy(stack=False)
        else:
            board_to_show = progression.copy(stack=False)

        move_text = None
        if position_index > 0 and position_index - 1 < len(moves):
            move_text = moves[position_index - 1]

        _display_position(
            run,
            board_to_show,
            position_index,
            unicode=unicode,
            move_text=move_text,
            modules_w=modules_w,
            modules_b=modules_b,
        )

        if position_index < positions_to_show - 1 and position_index < len(moves):
            move_to_apply = moves[position_index]
            if not _apply_move(progression, move_to_apply):
                print(
                    f"Stopping early: could not apply move '{move_to_apply}' at index {position_index}.",
                    file=sys.stderr,
                )
                break

            if position_index + 1 < len(fens):
                expected_fen = _normalise_fen(fens[position_index + 1])
                try:
                    expected_board = chess.Board(expected_fen)
                except ValueError:
                    expected_board = None
                if expected_board and progression.fen() != expected_board.fen():
                    print(
                        "Warning: reconstructed position does not match FEN from log at index "
                        f"{position_index + 1}.",
                        file=sys.stderr,
                    )

        if step and position_index < positions_to_show - 1:
            try:
                response = input("Press <Enter> for next move, 'a' to show all, 'q' to quit: ")
            except EOFError:
                response = "q"
            response = response.strip().lower()
            if response == "q":
                break
            if response == "a":
                step = False

        if position_index < positions_to_show - 1:
            print("\n" + "-" * 80 + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        runs = load_runs(args.runs)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Failed to load runs: {exc}", file=sys.stderr)
        return 1

    run = _select_run(runs, game_id=args.game_id, index=args.index)
    if not run:
        return 1

    replay_run(run, unicode=args.unicode, step=not args.all, limit=args.limit)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
