"""
arena_threaded.py — багатопотокова арена між двома агентами.

Фічі:
- Друк діаграм ТІЛЬКИ у визначні моменти (та фінальну): фази, capture/retake, hanging, fork.
- SAN: рахуємо ДО push (san_before) — без assert-крешів.
- DIAGRAM_UNICODE=True: ♔♕♖♗♘♙ / ♚♛♜♝♞♟ у консолі.
- Usage-статистика DynamicBot (якщо агент її надає).
- Перф-метрики: середній branching factor L та L^2 за гру.
- Потокобезпечний запис у спільну статистику.
"""

from __future__ import annotations
import time
import threading
import logging
from typing import Dict, Tuple, List, Optional

import chess

from chess_ai.bot_agent import make_agent, get_agent_names

# ---------- Налаштування ----------
THREADS = 4
GAMES_PER_THREAD = 2

WHITE_AGENT = "DynamicBot"
BLACK_AGENT = "FortifyBot"

LOG_LEVEL = logging.INFO
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

# ---------- Потокобезпека ----------
STATS_LOCK = threading.Lock()   # запис у спільний stats_out

# ---------- Логгер ----------
def _setup_logging():
    fmt = "%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s"
    logging.basicConfig(level=LOG_LEVEL, format=fmt)

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
        pass
    return None

def agent_reset_usage(agent) -> None:
    """Скинути usage-лічильники перед новою грою (якщо агент підтримує)."""
    try:
        if hasattr(agent, "reset_usage_stats"):
            agent.reset_usage_stats()
    except Exception:
        pass

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

# ---------- Ігри у потоці ----------

def play_games(thread_id: int, games: int, stats_out: Dict[int, Tuple[int,int,int]]):
    logger = logging.getLogger()

    wins = losses = draws = 0

    # У кожному потоці — СВОЇ інстанси агентів (без спільного стану між потоками)
    white_agent = make_agent(WHITE_AGENT, chess.WHITE)
    black_agent = make_agent(BLACK_AGENT, chess.BLACK)

    for n in range(1, games + 1):
        start_game = time.time()
        board = chess.Board()

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

        # Основний цикл гри
        while not board.is_game_over():
            # Перф-метрики: L та L^2 до ходу (у цій позиції)
            if PERF_METRICS:
                L = sum(1 for _ in board.legal_moves)
                l_sum += L
                l2_sum += L * L
                pos_count += 1

            color_to_move = board.turn
            agent = white_agent if color_to_move == chess.WHITE else black_agent

            move = agent.choose_move(board)
            if move is None:
                break

            # --- ВСЕ, ЩО ПОТРЕБУЄ СТАРОЇ ПОЗИЦІЇ — РАХУЄМО ДО PUSH ---
            is_cap = board.is_capture(move)
            will_retake = bool(is_cap and last_capture_square is not None and move.to_square == last_capture_square)
            # ВАЖЛИВО: SAN тільки ДО push!
            san_before = board.san(move)

            # --- ХІД ---
            try:
                board.push(move)
            except Exception:
                # На всяк випадок, якщо агент повернув нелегальний Move
                break

            # --- ПОДІЇ ПІСЛЯ PUSH ---

            # 1) Перехід фази
            new_phase = current_phase(board)
            if PRINT_DIAGRAM and PRINT_ON_PHASE and new_phase != last_phase:
                logger.info(
                    f"PHASE: {last_phase} → {new_phase}\n" +
                    board_diagram(board, unicode=DIAGRAM_UNICODE)
                )
                last_phase = new_phase

            # 2) Capture / Retake (лог — san_before)
            if PRINT_DIAGRAM and is_cap and PRINT_ON_CAPTURE:
                tag = "RETAKE" if will_retake and PRINT_ON_RETAKE else "CAPTURE"
                logger.info(
                    f"{tag}: {san_before} on {chess.square_name(move.to_square)}\n" +
                    board_diagram(board, unicode=DIAGRAM_UNICODE)
                )
            # оновимо останню «клітину захоплення» для детекту retake на наступному плай
            last_capture_square = move.to_square if is_cap else None

            # 3) Атака на «висячу» фігуру
            if PRINT_DIAGRAM and PRINT_ON_HANGING:
                hang = detect_hanging_attacks(board, color_to_move)  # ми щойно ходили цим кольором
                if hang:
                    sq = hang[0]
                    pc = board.piece_at(sq)
                    sym = pc.symbol().upper() if pc else "?"
                    logger.info(
                        f"HANGING ATTACK: opponent {sym} is hanging at {chess.square_name(sq)}\n" +
                        board_diagram(board, unicode=DIAGRAM_UNICODE)
                    )

            # 4) Вилка конем/слоном (після нашого ходу)
            if PRINT_DIAGRAM and PRINT_ON_FORK:
                fork_tag = is_fork_after_move(board, move, color_to_move)
                if fork_tag:
                    logger.info(
                        f"FORK: {fork_tag} after {san_before}\n" +
                        board_diagram(board, unicode=DIAGRAM_UNICODE)
                    )

        # Підсумки
        total_time = time.time() - start_game
        res = board.result()
        full_moves = board.fullmove_number
        plys = len(board.move_stack)

        if res == "1-0": wins += 1
        elif res == "0-1": losses += 1
        else: draws += 1

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
            logger.info("FINAL DIAGRAM:\n" + board_diagram(board, unicode=DIAGRAM_UNICODE))

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

    # Запис підсумків потоку — під Lock
    with STATS_LOCK:
        stats_out[thread_id] = (wins, losses, draws)

# ---------- Запуск ----------

def main():
    _setup_logging()
    logger = logging.getLogger()

    names = set(get_agent_names())
    if WHITE_AGENT not in names or BLACK_AGENT not in names:
        logger.warning(f"Agents list: {sorted(names)}")
        raise SystemExit(f"Unknown agent(s). WHITE={WHITE_AGENT} BLACK={BLACK_AGENT}")

    threads: List[threading.Thread] = []
    stats: Dict[int, Tuple[int,int,int]] = {}

    t0 = time.time()
    for i in range(1, THREADS + 1):
        t = threading.Thread(
            target=play_games,
            name=f"Arena-{i}",
            args=(i, GAMES_PER_THREAD, stats),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total_time = time.time() - t0
    total_games = sum(sum(s) for s in stats.values())
    wins = sum(s[0] for s in stats.values())
    losses = sum(s[1] for s in stats.values())
    draws = sum(s[2] for s in stats.values())

    logger.info("")
    logger.info(f"Total games: {total_games} in {total_time:.1f}s  |  per thread: {GAMES_PER_THREAD} × {THREADS}")
    logger.info(f"Wins: {wins}, Losses: {losses}, Draws: {draws}")

if __name__ == "__main__":
    main()
