"""
arena.py — послідовна арена між двома агентами (без потоків).

Фічі:
- Друк діаграм ТІЛЬКИ у визначні моменти (та фінальну): фази, capture/retake, hanging, fork.
- SAN: рахуємо ДО push (san_before) — без assert-крешів.
- DIAGRAM_UNICODE=True: ♔♕♖♗♘♙ / ♚♛♜♝♞♟ у консолі.
- Usage-статистика DynamicBot (якщо агент її надає).
- Перф-метрики: середній branching factor L та L^2 за гру.
"""

from __future__ import annotations
from utils.usage_logger import record_usage
record_usage(__file__)

import time
import logging
from typing import Dict, Tuple, List, Optional, Any

import chess
import os
import json
import traceback
from datetime import datetime

from chess_ai.bot_agent import make_agent, get_agent_names
from core.pst_trainer import update_from_board, update_from_history
from main import annotated_board

# ---------- Налаштування ----------
GAMES = 2

# Default internal vs internal. Override to pit against external engine.
WHITE_AGENT = "DynamicBot"
BLACK_AGENT = "FortifyBot"

LOG_LEVEL = logging.INFO
# Optional per-move time limit in seconds. If <= 0, disabled.
MOVE_TIME_LIMIT_S: float = float(os.getenv("CHESS_MOVE_TIME_LIMIT_S", "0"))
PERF_METRICS = True       # середній branching factor L та L^2 за гру
SAN_AFTER_EACH_GAME = True

PRINT_DIAGRAM = True      # друкувати діаграми у визначні моменти + фінальну
DIAGRAM_UNICODE = True    # ♔♕♖… замість ASCII

# Події, на які друкуємо діаграму (якщо PRINT_DIAGRAM=True)
PRINT_ON_PHASE    = True   # opening→midgame→endgame
PRINT_ON_CAPTURE  = True
PRINT_ON_RETAKE   = True
PRINT_ON_HANGING  = True
PRINT_ON_FORK     = True   # knight/bishop double-attack (після нашого ходу)

# Евристика фаз (можна підкрутити під свій смак)
MIDGAME_NONKING_PIECES_MAX   = 20   # >20 = opening
ENDGAME_NONKING_PIECES_MAX   = 12   # <=12 = endgame

# ---------- Логгер ----------
def _setup_logging():
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(level=LOG_LEVEL, format=fmt)

logger = logging.getLogger(__name__)

# ---------- Утиліти ----------

def moves_san_string(board: chess.Board) -> str:
    """Побудувати SAN для всієї партії з нуля (стабільний спосіб)."""
    temp = chess.Board()
    parts = []
    for mv in board.move_stack:
        parts.append(temp.san(mv))
        temp.push(mv)
    out = []
    for i, san in enumerate(parts, start=1):
        if i % 2 == 1:
            move_no = (i + 1) // 2
            out.append(f"{move_no}. {san}")
        else:
            out.append(san)
    return " ".join(out)

def board_diagram(board: chess.Board, unicode: bool = False) -> str:
    """
    Побудова діаграми позиції.
    Якщо unicode=True — використовує ♔♕♖♗♘♙ / ♚♛♜♝♞♟, інакше ASCII.
    """
    if unicode:
        U_WHITE = {chess.KING:"♔", chess.QUEEN:"♕", chess.ROOK:"♖",
                   chess.BISHOP:"♗", chess.KNIGHT:"♘", chess.PAWN:"♙"}
        U_BLACK = {chess.KING:"♚", chess.QUEEN:"♛", chess.ROOK:"♜",
                   chess.BISHOP:"♝", chess.KNIGHT:"♞", chess.PAWN:"♟"}
        def cell_symbol(sq: int) -> str:
            p = board.piece_at(sq)
            if not p: return "·"
            return U_WHITE[p.piece_type] if p.color == chess.WHITE else U_BLACK[p.piece_type]
    else:
        def cell_symbol(sq: int) -> str:
            p = board.piece_at(sq)
            if not p: return "."
            return p.symbol()

    lines: List[str] = []
    sep = "  +---+---+---+---+---+---+---+---+"
    lines.append(sep)
    for rank in range(7, -1, -1):
        row = []
        for file in range(8):
            sq = chess.square(file, rank)
            row.append(cell_symbol(sq))
        lines.append(f"{rank+1} | " + " | ".join(row) + " |")
        lines.append(sep)
    files = "    " + "   ".join("abcdefgh")
    lines.append(files)
    return "\n".join(lines)

def agent_usage_stats(agent) -> Optional[Dict[str,int]]:
    """Спроба дістати usage-статистику з адаптера (DynamicBot через MoveOnlyAdapter)."""
    try:
        if hasattr(agent, "get_usage_stats"):
            return agent.get_usage_stats()
    except Exception:
        logger.warning("Failed to get usage stats from %s", getattr(agent, '__class__', type(agent)))
    return None

def agent_reset_usage(agent) -> None:
    """Скинути usage-лічильники перед новою грою (якщо агент підтримує)."""
    try:
        if hasattr(agent, "reset_usage_stats"):
            agent.reset_usage_stats()
    except Exception:
        logger.warning("Failed to reset usage stats for %s", getattr(agent, '__class__', type(agent)))

# ---------- Виявлення подій ----------

def current_phase(board: chess.Board) -> str:
    """Оцінимо фазу за числом НЕ-королівських фігур (обох сторін)."""
    count = 0
    for pc in board.piece_map().values():
        if pc.piece_type != chess.KING:
            count += 1
    if count <= ENDGAME_NONKING_PIECES_MAX:
        return "endgame"
    if count <= MIDGAME_NONKING_PIECES_MAX:
        return "midgame"
    return "opening"

def detect_hanging_attacks(board: chess.Board, mover_color: bool) -> List[int]:
    """
    Знайти клітини з фігурами суперника, які ПІСЛЯ нашого ходу:
    - атакуються нами
    - не мають захисту суперника.
    Повертаємо список квадратів-цілей (int).
    """
    enemy = not mover_color
    out: List[int] = []
    for sq, pc in board.piece_map().items():
        if pc.color != enemy:
            continue
        if board.is_attacked_by(mover_color, sq) and len(board.attackers(enemy, sq)) == 0:
            out.append(sq)
    return out

def is_fork_after_move(board: chess.Board, last_move: chess.Move, mover_color: bool) -> Optional[str]:
    """
    Перевіряє, чи останній хід створив «вилку» для коня або слона:
    нападник (кінь/слон) одночасно б'є >=2 цінні цілі (K,Q,R,B,N).
    Повертає тег, напр. 'N:Q+R' або 'B:K+N', або None якщо ні.
    """
    p = board.piece_at(last_move.to_square)
    if not p or p.color != mover_color:
        return None
    if p.piece_type not in (chess.KNIGHT, chess.BISHOP):
        return None

    enemy = not mover_color
    attacked_syms: List[str] = []
    for t in board.attacks(last_move.to_square):
        pc = board.piece_at(t)
        if pc and pc.color == enemy and pc.piece_type in (chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
            attacked_syms.append({chess.KING:"K", chess.QUEEN:"Q", chess.ROOK:"R",
                                  chess.BISHOP:"B", chess.KNIGHT:"N"}[pc.piece_type])
    if len(attacked_syms) < 2:
        return None
    attacked_syms.sort(key=lambda s: "KQRBN".index(s))
    return f"{'N' if p.piece_type==chess.KNIGHT else 'B'}:{attacked_syms[0]}+{attacked_syms[1]}"

# ---------- Ігри (послідовно) ----------

def play_games(games: int) -> Tuple[int, int, int]:
    logger = logging.getLogger()

    wins = losses = draws = 0

    white_agent = make_agent(WHITE_AGENT, chess.WHITE)
    black_agent = make_agent(BLACK_AGENT, chess.BLACK)

    for n in range(1, games + 1):
        start_game = time.time()
        board = chess.Board()

        moves_log: List[str] = []
        fens_log: List[str] = []
        modules_w: List[str] = []
        modules_b: List[str] = []

        # usage-лічильники — з нуля
        agent_reset_usage(white_agent)
        agent_reset_usage(black_agent)

        # Перф-метрики
        pos_count = 0
        l_sum = 0
        l2_sum = 0

        # Для подій
        last_phase = current_phase(board)
        last_capture_square: Optional[int] = None  # для детекту retake (розміну)
        last_move_san: Optional[str] = None
        last_reason: str = ""
        # Результат/збій для цієї гри
        res: Optional[str] = None
        failure_info_game: Optional[Dict[str, Any]] = None

        # Основний цикл гри
        while not board.is_game_over():
            # Перф-метрики: L та L^2 до ходу (у цій позиції)
            if PERF_METRICS:
                L = board.legal_moves.count()
                l_sum += L
                l2_sum += L * L
                pos_count += 1

            color_to_move = board.turn
            agent = white_agent if color_to_move == chess.WHITE else black_agent

            # --- Вибір ходу з тайм-аутом та обробкою помилок ---
            technical_result: Optional[str] = None
            failure_info: Optional[Dict[str, Any]] = None

            start_choose = time.time()
            try:
                move = agent.choose_move(board)
            except Exception as ex:
                # Краш агента → технічна поразка сторони, що ходила
                tb = traceback.format_exc()
                loser_is_white = (color_to_move == chess.WHITE)
                technical_result = "0-1" if loser_is_white else "1-0"
                failure_info = {
                    "kind": "crash",
                    "side": "white" if loser_is_white else "black",
                    "agent": getattr(agent, "__class__", type(agent)).__name__,
                    "message": str(ex),
                    "traceback": tb,
                }
                logger.exception(
                    "Agent crash by %s (%s); awarding technical loss",
                    "white" if loser_is_white else "black",
                    failure_info["agent"],
                )
                # Finalize outside the loop
                reason = ""
                last_reason = "Agent crash"
                last_move_san = None
                # Jump to end-of-game handling
                res = technical_result
                failure_info_game = failure_info
                break
            elapsed_choose = time.time() - start_choose

            if MOVE_TIME_LIMIT_S > 0 and elapsed_choose > MOVE_TIME_LIMIT_S:
                # Перевищення ліміту часу → технічна поразка
                loser_is_white = (color_to_move == chess.WHITE)
                technical_result = "0-1" if loser_is_white else "1-0"
                failure_info = {
                    "kind": "timeout",
                    "side": "white" if loser_is_white else "black",
                    "agent": getattr(agent, "__class__", type(agent)).__name__,
                    "elapsed": elapsed_choose,
                    "limit": MOVE_TIME_LIMIT_S,
                }
                logger.error(
                    "Timeout %.3fs > %.3fs by %s (%s); awarding technical loss",
                    elapsed_choose, MOVE_TIME_LIMIT_S,
                    "white" if loser_is_white else "black",
                    failure_info["agent"],
                )
                reason = ""
                last_reason = "Timeout"
                last_move_san = None
                res = technical_result
                failure_info_game = failure_info
                break

            if move is None:
                # Агент не повернув хід → технічна поразка
                loser_is_white = (color_to_move == chess.WHITE)
                technical_result = "0-1" if loser_is_white else "1-0"
                failure_info = {
                    "kind": "no_move",
                    "side": "white" if loser_is_white else "black",
                    "agent": getattr(agent, "__class__", type(agent)).__name__,
                }
                logger.error(
                    "Agent returned None move by %s (%s); awarding technical loss",
                    "white" if loser_is_white else "black",
                    failure_info["agent"],
                )
                reason = ""
                last_reason = "No move"
                last_move_san = None
                res = technical_result
                failure_info_game = failure_info
                break

            # Перевірка легальності ДО розрахунку SAN
            if move not in board.legal_moves:
                loser_is_white = (color_to_move == chess.WHITE)
                technical_result = "0-1" if loser_is_white else "1-0"
                failure_info = {
                    "kind": "illegal_move",
                    "side": "white" if loser_is_white else "black",
                    "agent": getattr(agent, "__class__", type(agent)).__name__,
                    "move": getattr(move, "uci", lambda: str(move))(),
                }
                logger.error(
                    "Illegal move (pre-check) %s by %s (%s); awarding technical loss",
                    failure_info["move"],
                    "white" if loser_is_white else "black",
                    failure_info["agent"],
                )
                reason = ""
                last_reason = "Illegal move"
                last_move_san = None
                res = technical_result
                failure_info_game = failure_info
                break

            reason = agent.get_last_reason() if hasattr(agent, "get_last_reason") else ""

            # --- ВСЕ, ЩО ПОТРЕБУЄ СТАРОЇ ПОЗИЦІЇ — РАХУЄМО ДО PUSH ---
            is_cap = board.is_capture(move)
            will_retake = bool(is_cap and last_capture_square is not None and move.to_square == last_capture_square)
            # ВАЖЛИВО: SAN тільки ДО push!
            try:
                san_before = board.san(move)
            except Exception as ex:
                # SAN обчислення впало — трактуємо як нелегальний хід
                loser_is_white = (color_to_move == chess.WHITE)
                technical_result = "0-1" if loser_is_white else "1-0"
                failure_info = {
                    "kind": "illegal_move",
                    "side": "white" if loser_is_white else "black",
                    "agent": getattr(agent, "__class__", type(agent)).__name__,
                    "move": getattr(move, "uci", lambda: str(move))(),
                    "message": str(ex),
                }
                logger.exception(
                    "Illegal move (SAN) %s by %s (%s); awarding technical loss",
                    failure_info.get("move"),
                    "white" if loser_is_white else "black",
                    failure_info["agent"],
                )
                reason = ""
                last_reason = "Illegal move"
                last_move_san = None
                res = technical_result
                failure_info_game = failure_info
                break

            # --- ХІД ---
            try:
                board.push(move)
            except Exception as ex:
                # Якщо push не вдався — технічна поразка
                loser_is_white = (color_to_move == chess.WHITE)
                technical_result = "0-1" if loser_is_white else "1-0"
                failure_info = {
                    "kind": "illegal_move",
                    "side": "white" if loser_is_white else "black",
                    "agent": getattr(agent, "__class__", type(agent)).__name__,
                    "move": getattr(move, "uci", lambda: str(move))(),
                    "message": str(ex),
                }
                logger.exception(
                    "Illegal move %s by %s (%s); awarding technical loss",
                    failure_info.get("move"),
                    "white" if loser_is_white else "black",
                    failure_info["agent"],
                )
                res = technical_result
                break

            moves_log.append(san_before)
            fens_log.append(board.fen())
            if color_to_move == chess.WHITE:
                modules_w.append(reason)
            else:
                modules_b.append(reason)

            last_move_san = san_before
            if isinstance(reason, str):
                last_reason = reason
            elif reason:
                last_reason = str(reason)
            else:
                last_reason = ""

            def log_board_event(description: str, extra: Optional[List[str]] = None) -> None:
                info: List[str] = [description]
                if extra:
                    info.extend([line for line in extra if line])
                info.append(f"FEN: {board.fen()}")
                info.append(f"Last move: {san_before}")
                reason_text = last_reason.strip()
                if reason_text:
                    reason_parts = reason_text.splitlines()
                    info.append(f"Reason: {reason_parts[0]}")
                    info.extend(reason_parts[1:])
                logger.info(
                    annotated_board(
                        board,
                        info,
                        unicode=DIAGRAM_UNICODE,
                    )
                )

            # --- ПОДІЇ ПІСЛЯ PUSH ---

            # 1) Перехід фази
            new_phase = current_phase(board)
            if PRINT_DIAGRAM and PRINT_ON_PHASE and new_phase != last_phase:
                prev_phase = last_phase
                log_board_event(f"Phase: {prev_phase} → {new_phase}")
                last_phase = new_phase

            # 2) Capture / Retake (лог — san_before)
            if PRINT_DIAGRAM and is_cap and PRINT_ON_CAPTURE:
                tag = "RETAKE" if will_retake and PRINT_ON_RETAKE else "CAPTURE"
                log_board_event(f"{tag}: {chess.square_name(move.to_square)}")
            # оновимо останню «клітину захоплення» для детекту retake на наступному плай
            last_capture_square = move.to_square if is_cap else None

            # 3) Атака на «висячу» фігуру
            if PRINT_DIAGRAM and PRINT_ON_HANGING:
                hang = detect_hanging_attacks(board, color_to_move)  # ми щойно ходили цим кольором
                if hang:
                    sq = hang[0]
                    pc = board.piece_at(sq)
                    sym = pc.symbol().upper() if pc else "?"
                    log_board_event(
                        "Hanging attack",
                        extra=[f"Target: opponent {sym} at {chess.square_name(sq)}"],
                    )

            # 4) Вилка конем/слоном (після нашого ходу)
            if PRINT_DIAGRAM and PRINT_ON_FORK:
                fork_tag = is_fork_after_move(board, move, color_to_move)
                if fork_tag:
                    log_board_event("Fork detected", extra=[f"Pattern: {fork_tag}"])

        # Підсумки
        total_time = time.time() - start_game
        # Якщо сталася технічна поразка — res вже визначено вище
        if res is None:
            res = board.result()
        full_moves = board.fullmove_number
        plys = len(board.move_stack)

        if res == "1-0":
            wins += 1
        elif res == "0-1":
            losses += 1
        else:
            draws += 1

        # PST training: update tables after a decisive game
        if res in ("1-0", "0-1"):
            winner = chess.WHITE if res == "1-0" else chess.BLACK
            update_from_board(board, winner)
            update_from_history(list(board.move_stack), winner, steps=[15, 21, 35])

        # Лог: фініш гри
        logger.info(
            f"Game {n} finished | White={WHITE_AGENT} vs Black={BLACK_AGENT} "
            f"| Result={res} | Moves={full_moves} ({plys} ply) | Time={total_time:.2f}s"
        )

        # SAN (за бажанням)
        if SAN_AFTER_EACH_GAME:
            logger.info(f"SAN: {moves_san_string(board)}")

        # Фінальна діаграма
        if PRINT_DIAGRAM:
            final_info: List[str] = [
                "FINAL DIAGRAM",
                f"Result: {res}",
                f"FEN: {board.fen()}",
            ]
            if last_move_san:
                final_info.append(f"Last move: {last_move_san}")
            reason_text = last_reason.strip()
            if reason_text:
                reason_parts = reason_text.splitlines()
                final_info.append(f"Reason: {reason_parts[0]}")
                final_info.extend(reason_parts[1:])
            # If technical failure occurred, include concise details
            if failure_info_game:
                final_info.append(
                    f"Failure: {failure_info_game.get('kind')} by {failure_info_game.get('side')} ({failure_info_game.get('agent')})"
                )
                msg = failure_info_game.get('message')
                if msg:
                    final_info.append(f"Error: {msg}")
                if failure_info_game.get('kind') in ('illegal_move',) and failure_info_game.get('move'):
                    final_info.append(f"Move: {failure_info_game.get('move')}")
            final_info.append(f"Moves played: {full_moves} ({plys} ply)")
            final_info.append(f"Elapsed: {total_time:.2f}s")
            logger.info(
                annotated_board(
                    board,
                    final_info,
                    unicode=DIAGRAM_UNICODE,
                )
            )

        # Usage-статистика модулів (якщо є)
        w_stats = agent_usage_stats(white_agent)
        b_stats = agent_usage_stats(black_agent)
        if w_stats or b_stats:
            logger.info(f"USAGE: W={w_stats} | B={b_stats}")

        # Перф-метрики
        if PERF_METRICS and pos_count > 0:
            avg_L = l_sum / pos_count
            avg_L2 = l2_sum / pos_count
            logger.info(f"PERF: avg L={avg_L:.1f} | avg L^2={avg_L2:.1f} over {pos_count} positions")

        os.makedirs("runs", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_path = os.path.join("runs", f"{ts}.json")
        with open(run_path, "w", encoding="utf-8") as f:
            run_payload: Dict[str, Any] = {
                "moves": moves_log,
                "fens": fens_log,
                "modules_w": modules_w,
                "modules_b": modules_b,
                "result": res,
            }
            if failure_info_game:
                run_payload["failure"] = failure_info_game
            json.dump(
                run_payload,
                f,
                ensure_ascii=False,
                indent=2,
            )

    return wins, losses, draws

# ---------- Запуск ----------

def main():
    _setup_logging()
    logger = logging.getLogger()

    names = set(get_agent_names())
    if WHITE_AGENT not in names or BLACK_AGENT not in names:
        logger.warning(f"Agents list: {sorted(names)}")
        raise SystemExit(f"Unknown agent(s). WHITE={WHITE_AGENT} BLACK={BLACK_AGENT}")

    t0 = time.time()
    wins, losses, draws = play_games(GAMES)
    total_time = time.time() - t0
    total_games = GAMES

    logger.info("")
    logger.info(f"Total games: {total_games} in {total_time:.1f}s")
    logger.info(f"Wins: {wins}, Losses: {losses}, Draws: {draws}")

if __name__ == "__main__":
    main()

