# main.py
import textwrap
from itertools import zip_longest
from typing import List, Sequence

import chess
from bot_agent import DynamicBot
from evaluation import evaluate
from pst_tables import PST_MG, PIECE_VALUES


def annotated_board(
    board: chess.Board,
    info_lines: Sequence[str],
    *,
    unicode: bool = False,
    separator: str = "  │  ",
    info_width: int = 56,
    side_by_side: bool = True,
) -> str:
    """Return a board diagram with a side panel of supplementary data."""

    try:
        from arena_threaded import board_diagram as diagram_func  # local import to avoid cycle
    except ImportError:  # pragma: no cover - fallback for alternative entrypoints
        diagram_func = None

    if diagram_func is not None:
        diagram_text = diagram_func(board, unicode=unicode)
    else:
        diagram_text = board.unicode(borders=True) if hasattr(board, "unicode") else str(board)

    board_lines: List[str] = diagram_text.splitlines()
    board_width = max((len(line) for line in board_lines), default=0)

    wrapped_info: List[str] = []
    for raw_line in info_lines:
        if raw_line is None:
            continue
        text = str(raw_line)
        if not text:
            wrapped_info.append("")
            continue
        segments = text.splitlines() or [""]
        for segment in segments:
            if not segment:
                wrapped_info.append("")
                continue
            wrapped = textwrap.wrap(
                segment,
                width=info_width,
                break_long_words=False,
                break_on_hyphens=False,
            )
            if wrapped:
                wrapped_info.extend(wrapped)
            else:
                wrapped_info.append("")

    if not any(line.strip() for line in wrapped_info):
        return diagram_text

    if not side_by_side:
        info_text = "\n".join(wrapped_info).rstrip()
        if not info_text:
            return diagram_text
        if not diagram_text:
            return info_text
        return f"{diagram_text}\n\n{info_text}"

    combined: List[str] = []
    for board_line, info in zip_longest(board_lines, wrapped_info, fillvalue=""):
        left = board_line.ljust(board_width)
        combined.append(f"{left}{separator}{info}".rstrip())

    return "\n".join(combined)

def print_pst_summary():
    print("=== PST SUMMARY (midgame) ===")
    for pt, tbl in PST_MG.items():
        s = sum(tbl)
        mn = min(tbl)
        mx = max(tbl)
        print(f"PieceType {pt}: len={len(tbl)} sum={s} min={mn} max={mx}")
    print("Piece values:", PIECE_VALUES)
    print("=============================")

def run_match(max_plies: int = 40):
    board = chess.Board()
    white = DynamicBot("DynamicBot-White")
    black = DynamicBot("DynamicBot-Black")

    ply = 0
    print_pst_summary()
    print("Start FEN:", board.fen())
    print()

    while not board.is_game_over() and ply < max_plies:
        side = "White" if board.turn == chess.WHITE else "Black"
        bot = white if board.turn == chess.WHITE else black

        move, det = bot.select_move(board)
        board.push(move)
        ply += 1

        # Оцінка після зробленого ходу (позиція належить супернику):
        score, _ = evaluate(board)

        print(f"[Ply {ply:02d}] {side} {bot.name} played {board.peek().uci()}")
        print(f"  material={det['material']}  pst={det['pst']}  mobility={det['mobility']}  "
              f"att_w={det['attacks_white']} att_b={det['attacks_black']}  delta_att={det['delta_attacks']}")
        print(f"  eval_before_push(raw)≈{det['raw_score']}   eval_after={score}")
        print(f"  FEN: {board.fen()}")
        print("-")

    print("Result:", board.result(claim_draw=True))
    print("Game over reason:",
          "checkmate" if board.is_checkmate() else
          "stalemate" if board.is_stalemate() else
          "insufficient material" if board.is_insufficient_material() else
          "seventyfive-move" if board.is_seventyfive_moves() else
          "fivefold repetition" if board.is_fivefold_repetition() else
          "move limit reached"
    )

if __name__ == "__main__":
    # 40 плайів = 20 ходів кожної сторони. Зміни якщо треба.
    run_match(max_plies=40)
