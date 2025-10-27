# main.py
import textwrap
from itertools import zip_longest
from typing import List, Sequence, Optional
import argparse

import chess
from bot_agent import DynamicBot
from utils.metrics_sidebar import build_sidebar_metrics
from evaluation import evaluate
from metrics.attack_map import attack_count_per_square
from chess_ai.threat_map import ThreatMap
from core.evaluator import Evaluator
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
    white_bot: Optional[object] = None,
    black_bot: Optional[object] = None,
):
    board = chess.Board()
    white = white_bot or DynamicBot("DynamicBot-White")
    black = black_bot or DynamicBot("DynamicBot-Black")

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
            # Додатково: L^2 для продуктивності
            _update_metric("branching_L2", int(legal_count * legal_count))
        except Exception:
            pass
        bot = white if board.turn == chess.WHITE else black

        # Оцінка ДО ходу (raw)
        try:
            pre_score, det_before = evaluate(board)
        except Exception:
            pre_score, det_before = 0, {}

        move, move_info = bot.select_move(board)
        if move is None:
            try:
                move = next(iter(board.legal_moves))
            except StopIteration:
                move = None
        if move is None:
            # Немає легальних ходів — гра закінчилась.
            break

        board.push(move)
        ply += 1

        # Оцінка ПІСЛЯ ходу (позиція належить супернику):
        try:
            post_score, det_after = evaluate(board)
        except Exception:
            post_score, det_after = 0, {}

        print(f"[Ply {ply:02d}] {side} {getattr(bot, 'name', type(bot).__name__)} played {board.peek().uci()}")
        if det_after:
            print(
                f"  material={det_after.get('material', 'n/a')}  pst={det_after.get('pst', 'n/a')}  mobility={det_after.get('mobility', 'n/a')}  "
                f"att_w={det_after.get('attacks_white', 'n/a')} att_b={det_after.get('attacks_black', 'n/a')}  delta_att={det_after.get('delta_attacks', 'n/a')}"
            )
        # Пояснення ходу (для StockfishBot то буде reason)
        reason_text = ""
        try:
            if isinstance(move_info, dict) and move_info.get("reason"):
                reason_text = f"  reason: {move_info['reason']}\n"
        except Exception:
            pass
        print(f"  eval_before_push(raw)≈{pre_score}   eval_after={post_score}")
        if reason_text:
            print(reason_text, end="")
        print(f"  FEN: {board.fen()}")
        print("-")

        # Актуалізуємо агреговані метрики (за станом після ходу)
        try:
            _update_metric("material", int(det_after.get("material", 0)))
            _update_metric("pst", int(det_after.get("pst", 0)))
            _update_metric("mobility", int(det_after.get("mobility", 0)))
            _update_metric("attacks_white", int(det_after.get("attacks_white", 0)))
            _update_metric("attacks_black", int(det_after.get("attacks_black", 0)))
            _update_metric("delta_attacks", int(det_after.get("delta_attacks", 0)))
        except Exception:
            pass

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

        # Додаткові метрики: king safety / щільність загроз біля короля / ThreatMap / strong/weak control
        try:
            counts = attack_count_per_square(board)

            # King safety (оцінка безпеки короля для кожного кольору)
            ks_w = int(Evaluator.king_safety(board, chess.WHITE))
            ks_b = int(Evaluator.king_safety(board, chess.BLACK))
            _update_metric("king_safety_white", ks_w)
            _update_metric("king_safety_black", ks_b)

            # Щільність загроз біля короля (сума атак в радіусі 2 клітини навколо короля)
            def _king_threat_density(color: bool) -> int:
                ksq = board.king(color)
                if ksq is None:
                    return 0
                enemy = not color
                total = 0
                for sq in chess.SQUARES:
                    if chess.square_distance(sq, ksq) <= 2:
                        total += counts[enemy][sq]
                return int(total)

            _update_metric("king_threat_density_white", _king_threat_density(chess.WHITE))
            _update_metric("king_threat_density_black", _king_threat_density(chess.BLACK))

            # ThreatMap: тонкі фігури та пікові атаки/захист
            t_w = ThreatMap(chess.WHITE).summary(board)
            t_b = ThreatMap(chess.BLACK).summary(board)
            _update_metric("threatmap_thin_white", len(t_w.get("thin_pieces") or []))
            _update_metric("threatmap_thin_black", len(t_b.get("thin_pieces") or []))

            max_att_white = int(max(counts[chess.WHITE])) if counts[chess.WHITE] else 0
            max_att_black = int(max(counts[chess.BLACK])) if counts[chess.BLACK] else 0
            _update_metric("threatmap_max_attacked_white", max_att_white)
            _update_metric("threatmap_max_attacked_black", max_att_black)
            # «max_defended» для кольору еквівалентне максимуму атак цього ж кольору
            _update_metric("threatmap_max_defended_white", max_att_white)
            _update_metric("threatmap_max_defended_black", max_att_black)

            # Strong/weak control: за різницею атак на клітину
            strong_w = weak_w = strong_b = weak_b = 0
            for sq in chess.SQUARES:
                diff = counts[chess.WHITE][sq] - counts[chess.BLACK][sq]
                if diff >= 2:
                    strong_w += 1
                elif diff > 0:
                    weak_w += 1
                if diff <= -2:
                    strong_b += 1
                elif diff < 0:
                    weak_b += 1
            _update_metric("strong_control_white", strong_w)
            _update_metric("weak_control_white", weak_w)
            _update_metric("strong_control_black", strong_b)
            _update_metric("weak_control_black", weak_b)
        except Exception:
            pass

        # Optional ASCII/Unicode board diagram every N plies with metrics
        if diagram_every and diagram_every > 0 and (ply % diagram_every == 0):
            info_lines: List[str] = [
                f"Ply {ply:02d}: {side} {getattr(bot, 'name', type(bot).__name__)} {board.peek().uci()}",
                f"material={det_after.get('material', 'n/a')}  pst={det_after.get('pst', 'n/a')}  mobility={det_after.get('mobility', 'n/a')}",
                f"att_w={det_after.get('attacks_white', 'n/a')} att_b={det_after.get('attacks_black', 'n/a')}  delta_att={det_after.get('delta_attacks', 'n/a')}",
                f"eval_after={post_score}  raw≈{pre_score}",
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
            "branching_L2",
            "king_safety_white",
            "king_safety_black",
            "king_threat_density_white",
            "king_threat_density_black",
            "threatmap_thin_white",
            "threatmap_thin_black",
            "threatmap_max_attacked_white",
            "threatmap_max_attacked_black",
            "threatmap_max_defended_white",
            "threatmap_max_defended_black",
            "strong_control_white",
            "weak_control_white",
            "strong_control_black",
            "weak_control_black",
        ]
        for key in ordered_names:
            if key in metric_stats:
                print(" - " + _fmt(key))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a headless chess match between internal bots.")
    parser.add_argument("--max-plies", type=int, default=20, help="Maximum number of plies to play")
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
    parser.add_argument("--white", default="DynamicBot", help="White agent: DynamicBot or StockfishBot")
    parser.add_argument("--black", default="StockfishBot", help="Black agent: DynamicBot or StockfishBot")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unicode", action="store_true", help="Use Unicode chess symbols in diagrams")
    group.add_argument("--ascii", action="store_true", help="Force ASCII diagrams (default)")
    parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Do not include sidebar metrics in diagrams",
    )
    # Stockfish/engine options (used when either side is StockfishBot)
    # If not provided, StockfishBot will use $STOCKFISH_PATH or 'stockfish' from PATH
    parser.add_argument(
        "--sf-path",
        dest="sf_path",
        default=None,
        help="Path to stockfish binary (default: use $STOCKFISH_PATH or 'stockfish' on PATH)",
    )
    parser.add_argument("--sf-elo", dest="sf_elo", type=int, default=1600)
    parser.add_argument("--sf-skill", dest="sf_skill", type=int)
    parser.add_argument("--think-ms", dest="think_ms", type=int, default=150)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--hash-mb", dest="hash_mb", type=int, default=64)
    return parser.parse_args()


class _StockfishAdapter:
    """Adapter exposing select_move(...) for the main loop."""

    def __init__(
        self,
        color: bool,
        name: str,
        *,
        path: Optional[str] = None,
        think_time_ms: int = 200,
        skill_level: Optional[int] = None,
        uci_elo: Optional[int] = None,
        threads: int = 1,
        hash_mb: int = 128,
    ) -> None:
        from chess_ai.stockfish_bot import StockfishBot as _SF

        self.impl = _SF(
            color,
            path=path,
            think_time_ms=think_time_ms,
            skill_level=skill_level,
            uci_elo=uci_elo,
            threads=threads,
            hash_mb=hash_mb,
        )
        self.name = name

    def select_move(self, board: chess.Board):
        move, reason = self.impl.choose_move(board, debug=True)
        return move, {"reason": reason}

    def close(self) -> None:
        try:
            self.impl.close()
        except Exception:
            pass


def _make_bot_for_main(name: str, color: bool, *, side_label: str, args: argparse.Namespace):
    if name == "StockfishBot":
        return _StockfishAdapter(
            color,
            f"Stockfish-{side_label}",
            path=args.sf_path,
            think_time_ms=args.think_ms,
            skill_level=args.sf_skill,
            uci_elo=args.sf_elo,
            threads=args.threads,
            hash_mb=args.hash_mb,
        )
    # Default/fallback: DynamicBot
    return DynamicBot(f"DynamicBot-{side_label}")


if __name__ == "__main__":
    args = _parse_args()
    # У тестовому/повному режимі — без ліміту плаїв
    max_plies: int | None = None if (args.full_game or args.test_mode) else args.max_plies
    white_agent = _make_bot_for_main(getattr(args, "white", "DynamicBot"), chess.WHITE, side_label="White", args=args)
    black_agent = _make_bot_for_main(getattr(args, "black", "DynamicBot"), chess.BLACK, side_label="Black", args=args)
    run_match(
        max_plies=max_plies,
        diagram_every=(args.diagram_every if args.diagram_every > 0 else None),
        diagram_unicode=(True if args.unicode else False),
        include_metrics=(False if args.no_metrics else True),
        white_bot=white_agent,
        black_bot=black_agent,
    )
    try:
        if hasattr(white_agent, "close"):
            white_agent.close()
        if hasattr(black_agent, "close"):
            black_agent.close()
    except Exception:
        pass
