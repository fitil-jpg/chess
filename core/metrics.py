# metrics.py

"""Mirror of :mod:`metrics` for the :mod:`core` package."""

from __future__ import annotations

import chess


class MetricsManager:
    """Compute a few tiny heuristics for the given board state."""

    def __init__(self, board_state: chess.Board):
        self.board_state = board_state
        self.metrics = {"short_term": {}, "long_term": {}}

    def update_all_metrics(self) -> None:  # pragma: no cover - thin wrapper
        self.metrics["short_term"]["attacked_squares"] = self.count_attacked_squares()
        self.metrics["short_term"]["defended_pieces"] = self.count_defended_pieces()
        self.metrics["long_term"]["center_control"] = self.evaluate_center_control()
        self.metrics["long_term"]["king_safety"] = self.evaluate_king_safety()
        self.metrics["long_term"]["pawn_structure_stability"] = self.evaluate_pawn_structure()

    def count_attacked_squares(self) -> int:
        board = self.board_state
        white_attacks: chess.SquareSet = chess.SquareSet()
        black_attacks: chess.SquareSet = chess.SquareSet()
        for sq, piece in board.piece_map().items():
            if piece.color == chess.WHITE:
                white_attacks |= board.attacks(sq)
            else:
                black_attacks |= board.attacks(sq)
        return len(white_attacks) - len(black_attacks)

    def count_defended_pieces(self) -> int:
        board = self.board_state
        white_defended = 0
        black_defended = 0
        for sq, piece in board.piece_map().items():
            if board.attackers(piece.color, sq):
                if piece.color == chess.WHITE:
                    white_defended += 1
                else:
                    black_defended += 1
        return white_defended - black_defended

    def evaluate_center_control(self) -> int:
        board = self.board_state
        center = [chess.D4, chess.E4, chess.D5, chess.E5]
        score = 0
        for sq in center:
            piece = board.piece_at(sq)
            if piece and piece.color == chess.WHITE:
                score += 1
            if piece and piece.color == chess.BLACK:
                score -= 1
            if board.is_attacked_by(chess.WHITE, sq):
                score += 1
            if board.is_attacked_by(chess.BLACK, sq):
                score -= 1
        return score

    def evaluate_king_safety(self) -> int:
        board = self.board_state
        score = 0
        for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
            king_sq = board.king(color)
            if king_sq is None:
                continue
            attackers = len(board.attackers(not color, king_sq))
            defenders = len(board.attackers(color, king_sq))
            score += sign * (defenders - attackers)
        return score

    def evaluate_pawn_structure(self) -> int:
        board = self.board_state
        pawns: dict[bool, list[int]] = {chess.WHITE: [], chess.BLACK: []}
        for sq, piece in board.piece_map().items():
            if piece.piece_type == chess.PAWN:
                pawns[piece.color].append(sq)

        def is_passed(sq: int, color: bool, enemy_pawns: list[int]) -> bool:
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)
            for ep in enemy_pawns:
                ef = chess.square_file(ep)
                er = chess.square_rank(ep)
                if abs(ef - file) <= 1:
                    if color == chess.WHITE and er > rank:
                        return False
                    if color == chess.BLACK and er < rank:
                        return False
            return True

        score = 0
        for color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
            ours = pawns[color]
            files: dict[int, list[int]] = {}
            for sq in ours:
                files.setdefault(chess.square_file(sq), []).append(sq)

            isolated = 0
            doubled = 0
            passed = 0
            for file, sqs in files.items():
                if len(sqs) > 1:
                    doubled += len(sqs) - 1
                for sq in sqs:
                    if not files.get(file - 1) and not files.get(file + 1):
                        isolated += 1
                    if is_passed(sq, color, pawns[not color]):
                        passed += 1

            score += sign * (passed - isolated - doubled)
        return score

    def get_metrics(self):  # pragma: no cover - trivial accessor
        return self.metrics


class BoardMetrics:
    """Minimal metrics helper used in tests."""

    def __init__(self):
        self._metrics = {}

    def update_from_board(self, board, analyzer):  # pragma: no cover - trivial
        white = len(board.get_pieces('white'))
        black = len(board.get_pieces('black'))
        self._metrics['material_balance'] = white - black

    def get_metrics(self):  # pragma: no cover - trivial
        return self._metrics


__all__ = ["MetricsManager", "BoardMetrics"]

