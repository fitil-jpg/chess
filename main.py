# main.py
import textwrap
from itertools import zip_longest
from typing import List, Sequence
import argparse

import chess
from bot_agent import DynamicBot
from utils.metrics_sidebar import build_sidebar_metrics
from evaluation import evaluate
from pst_loader import effective_pst_for_piece, game_phase_from_board
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
        from arena import board_diagram as diagram_func  # local import to avoid cycle
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


def _pst_insights(board: chess.Board) -> List[str]:
    """Relate evaluation to PST numbers for current phase.

    Returns bullet-like lines: per-piece PST totals and top contributing cells.
    """
    phase = game_phase_from_board(board)

    per_piece: dict[int, int] = {pt: 0 for pt in range(1, 7)}
    cell_contribs: List[tuple[int, str]] = []  # (abs_val, display)
    sym = {
        chess.PAWN: "P",
        chess.KNIGHT: "N",
        chess.BISHOP: "B",
        chess.ROOK: "R",
        chess.QUEEN: "Q",
        chess.KING: "K",
    }

    for piece_type in range(1, 7):
        table = effective_pst_for_piece(piece_type, phase=phase)
        for sq in board.pieces(piece_type, chess.WHITE):
            v = int(table[sq])
            per_piece[piece_type] += v
            cell_contribs.append((abs(v), f"W {sym[piece_type]}{chess.square_name(sq)}:{v:+d}"))
        for sq in board.pieces(piece_type, chess.BLACK):
            v = -int(table[chess.square_mirror(sq)])
            per_piece[piece_type] += v
            cell_contribs.append((abs(v), f"B {sym[piece_type]}{chess.square_name(sq)}:{v:+d}"))

    summary = (
        f"PST[{phase}] per-piece: "
        f"P={per_piece[chess.PAWN]:+d} N={per_piece[chess.KNIGHT]:+d} "
        f"B={per_piece[chess.BISHOP]:+d} R={per_piece[chess.ROOK]:+d} "
        f"Q={per_piece[chess.QUEEN]:+d} K={per_piece[chess.KING]:+d}"
    )

    cell_contribs.sort(key=lambda t: t[0], reverse=True)
    top_cells = ", ".join(text for _, text in cell_contribs[:4]) or "-"
    return [summary, f"Top PST cells: {top_cells}"]

def run_match(
    max_plies: int | None = 40,
    *,
    diagram_every: int | None = None,
    diagram_unicode: bool = False,
    include_metrics: bool = True,
):
    board = chess.Board()
    white = DynamicBot("DynamicBot-White")
    black = DynamicBot("DynamicBot-Black")

    ply = 0
    # Агрегація метрик за гру (середні/мін/макс по плайях)
    from typing import Dict
    metric_stats: Dict[str, dict] = {}

    def _update_metric(name: str, value: int) -> None:
        st = metric_stats.setdefault(
            name,
            {"sum": 0.0, "min": float("inf"), "max": float("-inf"), "count": 0.0},
        )
        st["sum"] += float(value)
        st["count"] += 1.0
        if value < st["min"]:
            st["min"] = value
        if value > st["max"]:
            st["max"] = value
    print_pst_summary()
    print("Start FEN:", board.fen())
    print()

    while not board.is_game_over() and (max_plies is None or ply < max_plies):
        side = "White" if board.turn == chess.WHITE else "Black"
        # Перф-метрика: branching factor (к-ть легальних ходів у цій позиції)
        try:
            legal_count = board.legal_moves.count()
            _update_metric("legal_moves", int(legal_count))
        except Exception:
            pass
        bot = white if board.turn == chess.WHITE else black

        move, det = bot.select_move(board)
        board.push(move)
        ply += 1

        # Оцінка після зробленого ходу (позиція належить супернику):
        score, _ = evaluate(board)

        print(f"[Ply {ply:02d}] {side} {bot.name} played {board.peek().uci()}")
        print(
            f"  material={det['material']}  pst={det['pst']}  mobility={det['mobility']}  "
            f"att_w={det['attacks_white']} att_b={det['attacks_black']}  delta_att={det['delta_attacks']}"
        )
        print(f"  eval_before_push(raw)≈{det['raw_score']}   eval_after={score}")
        print(f"  FEN: {board.fen()}")
        print("-")

        # Актуалізуємо агреговані метрики
        _update_metric("material", int(det["material"]))
        _update_metric("pst", int(det["pst"]))
        _update_metric("mobility", int(det["mobility"]))
        _update_metric("attacks_white", int(det["attacks_white"]))
        _update_metric("attacks_black", int(det["attacks_black"]))
        _update_metric("delta_attacks", int(det["delta_attacks"]))

        # Додатково: к-ть НАШИХ/ЇХНІХ фігур під ударом у поточній позиції
        try:
            pieces_under_attack_white = 0
            pieces_under_attack_black = 0
            for sq, piece in board.piece_map().items():
                if piece.color == chess.WHITE:
                    if board.is_attacked_by(chess.BLACK, sq):
                        pieces_under_attack_white += 1
                else:
                    if board.is_attacked_by(chess.WHITE, sq):
                        pieces_under_attack_black += 1
            _update_metric("pieces_under_attack_white", pieces_under_attack_white)
            _update_metric("pieces_under_attack_black", pieces_under_attack_black)
        except Exception:
            pass

        # Optional ASCII/Unicode board diagram every N plies with metrics
        if diagram_every and diagram_every > 0 and (ply % diagram_every == 0):
            info_lines: List[str] = [
                f"Ply {ply:02d}: {side} {bot.name} {board.peek().uci()}",
                f"material={det['material']}  pst={det['pst']}  mobility={det['mobility']}",
                f"att_w={det['attacks_white']} att_b={det['attacks_black']}  delta_att={det['delta_attacks']}",
                f"eval_after={score}  raw≈{det['raw_score']}",
                f"FEN: {board.fen()}",
            ]
            if include_metrics:
                try:
                    info_lines.extend(build_sidebar_metrics(board))
                except Exception:
                    # Metrics are optional; continue even if they fail
                    pass
            # Add PST insights for the current phase
            try:
                info_lines.extend(_pst_insights(board))
            except Exception:
                pass
            print(
                annotated_board(
                    board,
                    info_lines,
                    unicode=diagram_unicode,
                    side_by_side=True,
                )
            )

    # Cross-version compatibility for python-chess API differences.
    def _safe_result(b: chess.Board) -> str:
        try:
            return b.result(claim_draw=True)
        except TypeError:
            # Older python-chess versions don't accept claim_draw
            return b.result()

    def _has(board_obj: chess.Board, method_name: str) -> bool:
        method = getattr(board_obj, method_name, None)
        if not callable(method):
            return False
        try:
            return method()
        except TypeError:
            # Some versions require an optional count for is_repetition
            if method_name == "is_repetition":
                try:
                    return method(3)
                except Exception:
                    return False
            return False

    result_text = _safe_result(board)
    reason_text = (
        "checkmate"
        if board.is_checkmate()
        else "stalemate"
        if board.is_stalemate()
        else "insufficient material"
        if _has(board, "is_insufficient_material")
        else "seventyfive-move"
        if _has(board, "is_seventyfive_moves")
        else "fivefold repetition"
        if _has(board, "is_fivefold_repetition")
        else "repetition"
        if _has(board, "is_repetition")
        else "move limit reached"
    )
    print("Result:", result_text)
    print("Game over reason:", reason_text)

    # Print a final annotated board diagram with metrics and reason
    final_info: List[str] = [
        "FINAL POSITION",
        f"Result: {result_text}",
        f"Reason: {reason_text}",
        f"FEN: {board.fen()}",
        f"Moves played: {board.fullmove_number} ({len(board.move_stack)} ply)",
    ]
    if include_metrics:
        try:
            final_info.extend(build_sidebar_metrics(board))
        except Exception:
            pass
    # Always try to add PST insights at the end
    try:
        final_info.extend(_pst_insights(board))
    except Exception:
        pass
    print(
        annotated_board(
            board,
            final_info,
            unicode=diagram_unicode,
            side_by_side=True,
        )
    )

    # ——— Фінальний підсумок метрик за гру ———
    if metric_stats:
        print()
        print("=== ПІДСУМОК МЕТРИК ЗА ГРУ ===")
        print("(avg / min / max по плайях)")
        def _fmt(name: str) -> str:
            st = metric_stats.get(name)
            if not st or st["count"] <= 0:
                return f"{name}: n/a"
            avg = st["sum"] / st["count"]
            mn = st["min"] if st["min"] != float("inf") else 0
            mx = st["max"] if st["max"] != float("-inf") else 0
            return f"{name}: avg={avg:.1f}, min={int(mn)}, max={int(mx)}"

        ordered_names = [
            "material",
            "pst",
            "mobility",
            "attacks_white",
            "attacks_black",
            "delta_attacks",
            "pieces_under_attack_white",
            "pieces_under_attack_black",
            "legal_moves",
        ]
        for key in ordered_names:
            if key in metric_stats:
                print(" - " + _fmt(key))

        print()
        print("Що ще можемо рахувати:")
        print(" - щільність загроз біля короля (king safety)")
        print(" - карти загроз/захисту (ThreatMap: max_attacked/max_defended, thin pieces)")
        print(" - контроль сильних/слабких клітин (strong/weak control)")
        print(" - середній branching factor L, L^2 для продуктивності")

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a headless chess match between internal bots.")
    parser.add_argument("--max-plies", type=int, default=40, help="Maximum number of plies to play")
    parser.add_argument(
        "--full-game",
        action="store_true",
        help="Play until game is over (ignore --max-plies)",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Test mode: play full game and print end-of-game metrics summary",
    )
    parser.add_argument(
        "--diagram-every",
        type=int,
        default=0,
        help="Print ASCII/Unicode board every N plies (0 disables)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unicode", action="store_true", help="Use Unicode chess symbols in diagrams")
    group.add_argument("--ascii", action="store_true", help="Force ASCII diagrams (default)")
    parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Do not include sidebar metrics in diagrams",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    # У тестовому/повному режимі — без ліміту плаїв
    max_plies: int | None = None if (args.full_game or args.test_mode) else args.max_plies
    run_match(
        max_plies=max_plies,
        diagram_every=(args.diagram_every if args.diagram_every > 0 else None),
        diagram_unicode=(True if args.unicode else False),
        include_metrics=(False if args.no_metrics else True),
    )
