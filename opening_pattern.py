# opening_patterns.py
from __future__ import annotations
import chess
from typing import List, Tuple, Optional, Dict, Any, Set

COW_TAG = "COW"

class CowOpeningPlanner:
    """
    COW-етапи:
      1) пішаки: e3,d3 (чорним e6,d6)
      2) коні:   g3,b3 (чорним g6,b6)
      3) слони:  білі -> e2,d2,c4,f4 ; чорні -> e7,d7,c5,f5
         (лише якщо хід не лишає наших пішаків «висячими» і сам по собі не «висяк»)
    """

    def __init__(self, color: bool):
        self.color = color
        if color == chess.WHITE:
            self.pawn_targets: Set[int] = {chess.E3, chess.D3}
            self.knight_targets: Set[int] = {chess.G3, chess.B3}
            self.pawn_starts = {chess.E2: chess.E3, chess.D2: chess.D3}
            self.knight_waypoints = {
                chess.G1: [chess.E2, chess.H3, chess.F3],
                chess.B1: [chess.D2, chess.C3],
            }
            self.bishop_targets: Set[int] = {chess.E2, chess.D2, chess.C4, chess.F4}
        else:
            self.pawn_targets = {chess.E6, chess.D6}
            self.knight_targets = {chess.G6, chess.B6}
            self.pawn_starts = {chess.E7: chess.E6, chess.D7: chess.D6}
            self.knight_waypoints = {
                chess.G8: [chess.E7, chess.H6, chess.F6],
                chess.B8: [chess.D7, chess.C6],
            }
            self.bishop_targets = {chess.E7, chess.D7, chess.C5, chess.F5}

    # ---------- інтерфейс ----------
    def choose_move(self, board: chess.Board, debug: bool = True) -> Tuple[Optional[chess.Move], str]:
        if board.turn != self.color:
            return None, f"{COW_TAG}: not my turn"

        # етап 1: пішаки
        if not self._pawns_ok(board):
            m = self._best_pawn_step(board)
            if m:
                return (m, f"{COW_TAG}: pawn-step") if debug else (m, COW_TAG)

        # етап 2: коні
        if not self._knights_ok(board):
            m = self._best_knight_step(board)
            if m:
                return (m, f"{COW_TAG}: knight-step") if debug else (m, COW_TAG)

        # етап 3: слони (з анти-підвіс перевіркою)
        if not self._bishops_ok(board):
            m = self._best_bishop_step(board)
            if m:
                return (m, f"{COW_TAG}: bishop-step(safe)") if debug else (m, COW_TAG)

        return None, f"{COW_TAG}: complete"

    def is_complete(self, board: chess.Board) -> bool:
        return self._pawns_ok(board) and self._knights_ok(board) and self._bishops_ok(board)

    # ---------- етапи ----------
    def _pawns_ok(self, board: chess.Board) -> bool:
        return self._count_on(board, self.pawn_targets, chess.PAWN) >= 2
    def _knights_ok(self, board: chess.Board) -> bool:
        return self._count_on(board, self.knight_targets, chess.KNIGHT) >= 2
    def _bishops_ok(self, board: chess.Board) -> bool:
        # достатньо вивести хоча б одного слона з базової лінії
        for sq, p in board.piece_map().items():
            if p.color == self.color and p.piece_type == chess.BISHOP:
                if chess.square_rank(sq) != (0 if self.color else 7):
                    return True
        return False

    # ---------- pawn / knight ----------
    def _best_pawn_step(self, board: chess.Board) -> Optional[chess.Move]:
        best, score = None, -10**9
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color or p.piece_type != chess.PAWN:
                continue
            s = 0
            if self.pawn_starts.get(m.from_square) == m.to_square:
                s += 900
            elif m.to_square in self.pawn_targets:
                s += 600
            if self._dest_unsafe(board, m):
                s -= 400
            if s > score:
                best, score = m, s
        return best

    def _best_knight_step(self, board: chess.Board) -> Optional[chess.Move]:
        best, score = None, -10**9
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color or p.piece_type != chess.KNIGHT:
                continue
            s = 0
            if m.to_square in self.knight_targets:
                s += 800
            wps = self.knight_waypoints.get(m.from_square, [])
            if m.to_square in wps:
                s += 500 if wps.index(m.to_square) == 0 else 350
            if self._dest_unsafe(board, m):
                s -= 300
            if s > score:
                best, score = m, s
        return best

    # ---------- bishops із анти-підвіс логікою ----------
    def _best_bishop_step(self, board: chess.Board) -> Optional[chess.Move]:
        best, score = None, -10**9
        for m in board.legal_moves:
            p = board.piece_at(m.from_square)
            if not p or p.color != self.color or p.piece_type != chess.BISHOP:
                continue
            # пріоритетні точки
            s = 0
            if m.to_square in self.bishop_targets:
                s += 420
            # безпека клітини призначення
            if self._dest_unsafe(board, m):
                continue  # слона не ставимо «під підвіс»
            # перевірка: чи не лишаємо наших пішаків «висячими»
            if self._bishop_move_leaves_pawn_hanging(board, m):
                continue
            # маленький бонус за вихід з базової
            if chess.square_rank(m.from_square) == (0 if self.color else 7):
                s += 80
            if s > score:
                best, score = m, s
        return best

    # ---------- допоміжні ----------
    def _count_on(self, board: chess.Board, squares: set[int], ptype: int) -> int:
        c = 0
        for sq in squares:
            p = board.piece_at(sq)
            if p and p.color == self.color and p.piece_type == ptype:
                c += 1
        return c

    def _dest_unsafe(self, board: chess.Board, m: chess.Move) -> bool:
        tmp = board.copy(stack=False); tmp.push(m)
        att = len(tmp.attackers(not self.color, m.to_square))
        defn = len(tmp.attackers(self.color, m.to_square))
        return att > 0 and defn == 0

    def _bishop_move_leaves_pawn_hanging(self, board: chess.Board, m: chess.Move) -> bool:
        """Чи лишаємо будь-якого нашого пішака беззахисним, забираючи захист цим слоном?"""
        from_sq = m.from_square
        # Пішаки, яких цей слон захищає ДО ходу
        defended_pawns_before = self._our_pawns_defended_from(board, from_sq)
        if not defended_pawns_before:
            return False
        tmp = board.copy(stack=False); tmp.push(m)
        for psq in defended_pawns_before:
            defenders = len(tmp.attackers(self.color, psq))
            attackers = len(tmp.attackers(not self.color, psq))
            if attackers > 0 and defenders == 0:
                return True
        return False

    def _our_pawns_defended_from(self, board: chess.Board, bishop_sq: int) -> List[int]:
        res = []
        for sq in board.attacks(bishop_sq):
            p = board.piece_at(sq)
            if p and p.color == self.color and p.piece_type == chess.PAWN:
                # перевіримо, що МИ справді захисники того поля
                if bishop_sq in board.attackers(self.color, sq):
                    res.append(sq)
        return res
