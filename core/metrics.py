# metrics.py

"""Simple metrics helpers based on :mod:`python-chess`.

This module mirrors :mod:`metrics` but lives inside ``core`` so that internal
modules can use it.  Only a subset of evaluation logic is implemented to keep
unit tests light-weight."""

from __future__ import annotations

import chess


class MetricsManager:
    def __init__(self, board_state: chess.Board):
        self.board_state = board_state
        self.metrics = {
            "short_term": {},
            "long_term": {},
        }

    def update_all_metrics(self) -> None:
        self.metrics["short_term"]["attacked_squares"] = self.count_attacked_squares()
        self.metrics["short_term"]["defended_pieces"] = self.count_defended_pieces()
        self.metrics["long_term"]["center_control"] = self.evaluate_center_control()
        self.metrics["long_term"]["king_safety"] = self.evaluate_king_safety()
        self.metrics["long_term"]["pawn_structure_stability"] = self.evaluate_pawn_structure()

    # --- short term metrics -------------------------------------------------
    def count_attacked_squares(self) -> int:
        board = self.board_state
        white_attacked = chess.SquareSet()
        black_attacked = chess.SquareSet()
        for square, piece in board.piece_map().items():
            if piece.color == chess.WHITE:
                white_attacked |= board.attacks(square)
            else:
                black_attacked |= board.attacks(square)
        return len(white_attacked) - len(black_attacked)

    def count_defended_pieces(self) -> int:
        board = self.board_state
        white = black = 0
        for square, piece in board.piece_map().items():
            if piece.color == chess.WHITE:
                if board.is_attacked_by(chess.WHITE, square):
                    white += 1
            else:
                if board.is_attacked_by(chess.BLACK, square):
                    black += 1
        return white - black

    # --- long term metrics --------------------------------------------------
    def evaluate_center_control(self) -> int:
        board = self.board_state
        center = [chess.D4, chess.E4, chess.D5, chess.E5]
        white = black = 0
        for sq in center:
            piece = board.piece_at(sq)
            if piece:
                if piece.color == chess.WHITE:
                    white += 1
                else:
                    black += 1
            if board.is_attacked_by(chess.WHITE, sq):
                white += 1
            if board.is_attacked_by(chess.BLACK, sq):
                black += 1
        return white - black

    def evaluate_king_safety(self) -> int:
        board = self.board_state

        def threats(color: chess.Color) -> int:
            king_sq = board.king(color)
            if king_sq is None:
                return 0
            enemy = not color
            danger = 0
            for sq in chess.SquareSet(chess.KING_ATTACKS[king_sq]):
                piece = board.piece_at(sq)
                if piece and piece.color == enemy:
                    danger += 1
                elif board.is_attacked_by(enemy, sq):
                    danger += 1
            return danger

        black_threats = threats(chess.BLACK)
        white_threats = threats(chess.WHITE)
        return black_threats - white_threats

    def evaluate_pawn_structure(self) -> int:
        board = self.board_state

        def pawn_score(color: chess.Color) -> int:
            pawns = list(board.pieces(chess.PAWN, color))
            score = 0
            files = [chess.square_file(sq) for sq in pawns]
            for f in set(files):
                count = files.count(f)
                if count > 1:
                    score -= count - 1
            for sq in pawns:
                file = chess.square_file(sq)
                adj = {file - 1, file + 1}
                if not any(chess.square_file(other) in adj for other in pawns):
                    score -= 1
            return score

        white_score = pawn_score(chess.WHITE)
        black_score = pawn_score(chess.BLACK)
        return white_score - black_score

    def get_metrics(self):
        return self.metrics


class BoardMetrics:
    """Minimal metrics helper used in tests.

    Only a single metric – ``material_balance`` – is tracked.  The method
    :meth:`update_from_board` relies on :meth:`Board.get_pieces` to avoid direct
    access to the board's internal ``pieces`` list.
    """

    def __init__(self):
        self._metrics = {}

    def update_from_board(self, board, analyzer):  # pragma: no cover - trivial
        white = len(board.get_pieces('white'))
        black = len(board.get_pieces('black'))
        self._metrics['material_balance'] = white - black

    def get_metrics(self):  # pragma: no cover - trivial
        return self._metrics
