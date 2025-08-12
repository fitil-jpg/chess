# chess_ai/threat_guard.py
from __future__ import annotations
from typing import Optional, Tuple, List, Dict
import chess

# Які пари вважаємо «небезпечними» для 2-ходової загрози.
# Формат — unordered пара типів у буквах: {"K","Q"} == {"Q","K"}.
DANGEROUS_PAIRS: List[frozenset[str]] = [
    frozenset({"K", "Q"}),
    frozenset({"K", "R"}),
    frozenset({"K", "N"}),
    frozenset({"K", "P"}),   # король + пішак — як маркер проблем навколо короля
    frozenset({"B", "N"}),
    frozenset({"N", "P"}),
    # можна додавати інші за потреби
]

SYM_BY_PTYPE: Dict[int, str] = {
    chess.KING: "K", chess.QUEEN: "Q", chess.ROOK: "R",
    chess.BISHOP: "B", chess.KNIGHT: "N", chess.PAWN: "P",
}

VALUABLE_SET = {chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT}
# у «цінні» включили й коня/слона — щоб ловити B+N, N+P тощо.

def _sym_pair_is_danger(s1: str, s2: str) -> bool:
    return frozenset({s1, s2}) in DANGEROUS_PAIRS

def _targets_attacked_symbols(board: chess.Board, attacker_sq: int, our_color: bool) -> List[str]:
    """Повертає список літер фігур, які АТАКУЄ фігура з attacker_sq (після вже зробленого ходу)."""
    out: List[str] = []
    for t in board.attacks(attacker_sq):
        pc = board.piece_at(t)
        if pc and pc.color == our_color:
            out.append(SYM_BY_PTYPE[pc.piece_type])
    return out

def _enemy_knight_two_move_fork(board: chess.Board, our_color: bool) -> Tuple[bool, Optional[chess.Move], Optional[chess.Move], str]:
    """
    Чи може ворог КОНЕМ за 2 свої ходи (r1→r2) поставити вилку на небезпечну пару?
    Перебираємо ВСІ r1 конем → з позиції після r1 перебираємо легальні r2 тим самим конем.
    Перевіряємо, що з клітини r2.to_square кінь атакує >=2 наших «цінних» цілей і пара в списку DANGEROUS_PAIRS.
    """
    enemy = not our_color
    for r1 in board.legal_moves:
        p = board.piece_at(r1.from_square)
        if not p or p.color != enemy or p.piece_type != chess.KNIGHT:
            continue
        tmp1 = board.copy(stack=False); tmp1.push(r1)

        # усі наступні легальні ходи ЦИМ же конем
        for r2 in tmp1.legal_moves:
            if r2.from_square != r1.to_square:
                continue
            tmp2 = tmp1.copy(stack=False); tmp2.push(r2)
            # після r2 кінь стоїть на r2.to_square і атакує у L-патерні
            symbols = _targets_attacked_symbols(tmp2, r2.to_square, our_color)
            if len(symbols) < 2:
                continue
            # перевіримо КОЖНУ пару з атакованих
            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    if _sym_pair_is_danger(symbols[i], symbols[j]):
                        tag = f"N:{symbols[i]}+{symbols[j]}"
                        return True, r1, r2, tag
    return False, None, None, ""

def _enemy_bishop_two_move_double(board: chess.Board, our_color: bool) -> Tuple[bool, Optional[chess.Move], Optional[chess.Move], str]:
    """
    Грубий детектор «подвійної атаки» слоном за 2 ходи: r1 — розгортання слона, r2 — хід слоном так,
    що він одночасно б'є дві наші цінні фігури (напр., B+N).
    """
    enemy = not our_color
    for r1 in board.legal_moves:
        p = board.piece_at(r1.from_square)
        if not p or p.color != enemy or p.piece_type != chess.BISHOP:
            continue
        tmp1 = board.copy(stack=False); tmp1.push(r1)
        for r2 in tmp1.legal_moves:
            if r2.from_square != r1.to_square:
                continue
            tmp2 = tmp1.copy(stack=False); tmp2.push(r2)
            symbols = _targets_attacked_symbols(tmp2, r2.to_square, our_color)
            if len(symbols) < 2:
                continue
            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    if _sym_pair_is_danger(symbols[i], symbols[j]):
                        tag = f"B:{symbols[i]}+{symbols[j]}"
                        return True, r1, r2, tag
    return False, None, None, ""

def _enemy_pawn_two_move_threat(board: chess.Board, our_color: bool) -> Tuple[bool, Optional[chess.Move], Optional[chess.Move], str]:
    """
    Чи може ворог ПІШАКОМ за 2 свої ходи створити явну загрозу: після r1 (push/cap)
    на r2 пішаки мають ЛЕГАЛЬНЕ взяття нашої Q / R / B / N (або атака на К)?
    Спрощено: шукаємо r2-пішак-взяття цінної фігури. Це «дешева й надійна» евристика.
    """
    enemy = not our_color
    for r1 in board.legal_moves:
        p = board.piece_at(r1.from_square)
        if not p or p.color != enemy or p.piece_type != chess.PAWN:
            continue
        tmp1 = board.copy(stack=False); tmp1.push(r1)

        # шукаємо ЛЕГАЛЬНИЙ r2 саме ЦИМ же пішаком
        for r2 in tmp1.legal_moves:
            if r2.from_square != r1.to_square:
                continue
            # цікавлять діагональні взяття
            if chess.square_file(r2.from_square) == chess.square_file(r2.to_square):
                continue
            before = tmp1.piece_at(r2.to_square)
            if before and before.color == our_color:
                sym = SYM_BY_PTYPE[before.piece_type]
                if sym in ("Q", "R", "B", "N"):        # сильна ціль
                    return True, r1, r2, f"P:x{sym}"
                if sym == "K":                         # біля короля — теж тригер
                    return True, r1, r2, "P:K"
        # Додатково: якщо після r1 пішаки вже АТАКУЮТЬ (без обов'язкового взяття) нашу Q/K — теж тригер
        to_sq = r1.to_square
        qsq = _find_piece(tmp1, our_color, chess.QUEEN)
        ksq = _find_piece(tmp1, our_color, chess.KING)
        for a in tmp1.attacks(to_sq):
            if a == qsq:
                return True, r1, None, "P->Q(next)"
            if a == ksq:
                return True, r1, None, "P->K(next)"
    return False, None, None, ""

def _find_piece(board: chess.Board, color: bool, ptype: int) -> Optional[int]:
    for sq, pc in board.piece_map().items():
        if pc.color == color and pc.piece_type == ptype:
            return sq
    return None

def enemy_two_move_fork_risk(board: chess.Board, our_color: bool) -> Tuple[bool, str, Optional[chess.Move], Optional[chess.Move]]:
    """
    Загальний фасад: перевіряємо у пріоритеті KNIGHT → BISHOP → PAWN.
    Повертає (risk, tag, r1, r2). Якщо r2 = None у пішака — це «наступним ходом атакує».
    """
    ok, r1, r2, tag = _enemy_knight_two_move_fork(board, our_color)
    if ok:
        return True, tag, r1, r2
    ok, r1, r2, tag = _enemy_bishop_two_move_double(board, our_color)
    if ok:
        return True, tag, r1, r2
    ok, r1, r2, tag = _enemy_pawn_two_move_threat(board, our_color)
    if ok:
        return True, tag, r1, r2
    return False, "", None, None

# TODO (на пізніше): форсування «en passant corridor» проти королівського щита.
# Ідея: наші пішаки займають клітини поруч/попереду «королівської пешки» ворога,
# змушуючи її йти на крок через бите поле (або провокуючи слабкість). Це вимагає вже планера.
