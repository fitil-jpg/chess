# metrics.py

"""Simple metrics helpers based on :mod:`python-chess`.

The original project only provided placeholders for the metrics.  For the unit
tests we implement a very small but functional subset that evaluates a given
``chess.Board``.  All metrics return ``int`` values where a positive number
favours White and a negative number favours Black.  The goal of these helpers is
not to be a perfect chess evaluation function but rather to exercise basic
usage of the ``chess`` package.
"""

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
        """Return the difference in attacked squares between White and Black."""
        board = self.board_state
        white_attacked = chess.SquareSet()
        black_attacked = chess.SquareSet()
        white_squares = {sq for sq, p in board.piece_map().items() if p.color == chess.WHITE}
        black_squares = {sq for sq, p in board.piece_map().items() if p.color == chess.BLACK}
        for square, piece in board.piece_map().items():
            attacks = board.attacks(square)
            if piece.color == chess.WHITE:
                white_attacked |= attacks - white_squares
            else:
                black_attacked |= attacks - black_squares
        return len(white_attacked) - len(black_attacked)

    def count_defended_pieces(self) -> int:
        """Return the difference in defended pieces between White and Black."""
        board = self.board_state
        white = black = 0
        for square, piece in board.piece_map().items():
            if piece.color == chess.WHITE:
                if board.attackers(chess.WHITE, square):
                    white += 1
            else:
                if board.attackers(chess.BLACK, square):
                    black += 1
        return white - black

    # --- long term metrics --------------------------------------------------
    def evaluate_center_control(self) -> int:
        """Evaluate control over the four central squares."""
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
            if board.attackers(chess.WHITE, sq):
                white += 1
            if board.attackers(chess.BLACK, sq):
                black += 1
        return white - black

    def evaluate_king_safety(self) -> int:
        """Measure king safety by counting attacks near each king."""
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
                elif board.attackers(enemy, sq):
                    danger += 1
            return danger

        black_threats = threats(chess.BLACK)
        white_threats = threats(chess.WHITE)
        return black_threats - white_threats

    def evaluate_pawn_structure(self) -> int:
        """Crude pawn structure evaluation (doubled & isolated pawns)."""
        board = self.board_state

        def pawn_score(color: chess.Color) -> int:
            pawns = list(board.pieces(chess.PAWN, color))
            score = 0
            files = [chess.square_file(sq) for sq in pawns]
            for f in set(files):
                count = files.count(f)
                if count > 1:
                    score -= count - 1  # doubled pawns
            for sq in pawns:
                file = chess.square_file(sq)
                adj = {file - 1, file + 1}
                if not any(chess.square_file(other) in adj for other in pawns):
                    score -= 1  # isolated pawn
            return score

        white_score = pawn_score(chess.WHITE)
        black_score = pawn_score(chess.BLACK)
        return white_score - black_score

    # ------------------------------------------------------------------
    def get_metrics(self):
        return self.metrics
