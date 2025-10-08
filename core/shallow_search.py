from __future__ import annotations

import chess
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

# Lightweight, dependency-free shallow search (2–3 ply) with:
# - Negamax with alpha–beta pruning
# - Quiescence (captures and checks)
# - Basic move ordering (hash move, MVV-LVA, killer, history)
# - Small transposition table


# Piece values for MVV-LVA (centipawns)
_MVV_LVA_VALUES = {
	chess.PAWN: 100,
	chess.KNIGHT: 320,
	chess.BISHOP: 330,
	chess.ROOK: 500,
	chess.QUEEN: 900,
	chess.KING: 20000,
}


def _material_eval(board: chess.Board) -> int:
	"""Very small evaluation function: material only, from side-to-move perspective."""
	score = 0
	turn = board.turn
	for pt, val in (
		(chess.PAWN, 100),
		(chess.KNIGHT, 300),
		(chess.BISHOP, 300),
		(chess.ROOK, 500),
		(chess.QUEEN, 900),
	):
		score += len(board.pieces(pt, turn)) * val
		score -= len(board.pieces(pt, not turn)) * val
	return score


def _order_moves(
	board: chess.Board,
	moves: Iterable[chess.Move],
	killers: Dict[int, List[chess.Move]],
	history: Dict[Tuple[int, int, int], int],
	ply: int,
	hash_move: Optional[chess.Move],
) -> List[chess.Move]:
	def score(move: chess.Move) -> int:
		if hash_move is not None and move == hash_move:
			return 1_000_000
		if board.is_capture(move):
			victim = board.piece_type_at(move.to_square)
			attacker = board.piece_type_at(move.from_square)
			v_val = _MVV_LVA_VALUES.get(victim, 0)
			a_val = _MVV_LVA_VALUES.get(attacker, 0)
			return 100_000 + v_val * 10 - a_val
		if move in killers.get(ply, []):
			return 90_000
		return history.get((board.turn, move.from_square, move.to_square), 0)

	return sorted(moves, key=score, reverse=True)


def _quiescence(board: chess.Board, alpha: int, beta: int) -> int:
	stand_pat = _material_eval(board)
	if stand_pat >= beta:
		return stand_pat
	if alpha < stand_pat:
		alpha = stand_pat

	for move in board.legal_moves:
		if not (board.is_capture(move) or board.gives_check(move)):
			continue
		board.push(move)
		score = -_quiescence(board, -beta, -alpha)
		board.pop()
		if score >= beta:
			return score
		if score > alpha:
			alpha = score
	return alpha


EXACT, LOWERBOUND, UPPERBOUND = 0, 1, 2


@dataclass
class _TTEntry:
	depth: int
	flag: int
	value: int
	move: Optional[chess.Move]


class ShallowSearch:
	"""Self-contained shallow search utility.

	Intended for quick tactical probes (2–3 ply) where it pays.
	The transposition table is intentionally small and reset per search.
	"""

	def __init__(self, tt_capacity: int = 1 << 16):
		self.tt: Dict[int, _TTEntry] = {}
		self.killers: Dict[int, List[chess.Move]] = {}
		self.history: Dict[Tuple[int, int, int], int] = {}
		self.tt_capacity = tt_capacity

	def _tt_get(self, key: int) -> Optional[_TTEntry]:
		return self.tt.get(key)

	def _tt_store(self, key: int, entry: _TTEntry) -> None:
		if len(self.tt) >= self.tt_capacity:
			# Simple aging: drop an arbitrary item
			self.tt.pop(next(iter(self.tt)))
		self.tt[key] = entry

	def _ab(
		self,
		board: chess.Board,
		depth: int,
		alpha: int,
		beta: int,
		ply: int,
	) -> Tuple[int, Optional[chess.Move]]:
		alpha_orig = alpha

		# TT probe (python-chess 1.11+ has no transposition_key; use fen hash)
		try:
			key = board.transposition_key()
		except Exception:
			key = hash(board.fen())
		entry = self._tt_get(key)
		hash_move: Optional[chess.Move] = None
		if entry and entry.depth >= depth:
			hash_move = entry.move
			if entry.flag == EXACT:
				return entry.value, hash_move
			if entry.flag == LOWERBOUND and entry.value > alpha:
				alpha = entry.value
			elif entry.flag == UPPERBOUND and entry.value < beta:
				beta = entry.value
			if alpha >= beta:
				return entry.value, hash_move

		# Leaf or terminal
		if depth == 0 or board.is_game_over():
			return _quiescence(board, alpha, beta), None

		best_val = -10**9
		best_move: Optional[chess.Move] = None

		moves = list(board.legal_moves)
		moves = _order_moves(board, moves, self.killers, self.history, ply, hash_move)

		for move in moves:
			board.push(move)
			score, _ = self._ab(board, depth - 1, -beta, -alpha, ply + 1)
			score = -score
			board.pop()

			if score > best_val:
				best_val = score
				best_move = move
			if score > alpha:
				alpha = score
			if alpha >= beta:
				# update killer/history on cutoff
				kl = self.killers.setdefault(ply, [])
				if move not in kl:
					kl.insert(0, move)
					del kl[2:]
				key_hist = (board.turn, move.from_square, move.to_square)
				self.history[key_hist] = self.history.get(key_hist, 0) + depth * depth
				break

		# store to TT
		flag = EXACT
		if best_val <= alpha_orig:
			flag = UPPERBOUND
		elif best_val >= beta:
			flag = LOWERBOUND
		self._tt_store(key, _TTEntry(depth, flag, best_val, best_move))
		return best_val, best_move

	def search(self, board: chess.Board, depth: int = 3) -> Tuple[int, Optional[chess.Move]]:
		"""Run a shallow search and return (score, best_move)."""
		self.tt.clear(); self.killers.clear(); self.history.clear()
		alpha, beta = -10**9, 10**9
		best_score, best_move = -10**9, None
		moves = _order_moves(board, list(board.legal_moves), self.killers, self.history, 0, None)
		for move in moves:
			board.push(move)
			score, _ = self._ab(board, depth - 1, -beta, -alpha, 1)
			score = -score
			board.pop()
			if score > best_score:
				best_score, best_move = score, move
			if score > alpha:
				alpha = score
		return best_score, best_move


__all__ = ["ShallowSearch"]

