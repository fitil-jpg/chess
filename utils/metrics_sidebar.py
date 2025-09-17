"""Helpers for building sidebar metrics for board visualisations."""

from __future__ import annotations

from typing import Dict, List

import chess

from chess_ai.threat_map import ThreatMap

__all__ = ["build_sidebar_metrics"]

_PIECE_NAME: Dict[chess.PieceType, str] = {
    chess.PAWN: "Pawns",
    chess.KNIGHT: "Knights",
    chess.BISHOP: "Bishops",
    chess.ROOK: "Rooks",
    chess.QUEEN: "Queen",
    chess.KING: "King",
}


def _format_square(value: int | None) -> str:
    if isinstance(value, int):
        return chess.square_name(value)
    return "-"


def _ensure_threat_map(
    threat_maps: Dict[chess.Color, ThreatMap] | None, color: chess.Color
) -> ThreatMap:
    if threat_maps is not None:
        existing = threat_maps.get(color)
        if existing is not None:
            return existing
        threat_maps[color] = ThreatMap(color)
        return threat_maps[color]
    return ThreatMap(color)


def _threat_map_summary(
    board: chess.Board, threat_maps: Dict[chess.Color, ThreatMap] | None
) -> str:
    tmap = _ensure_threat_map(threat_maps, board.turn)
    summary = tmap.summary(board)

    thin_list = summary.get("thin_pieces") or []
    thin_count = len(thin_list)

    if thin_count > 0:
        squares = ", ".join(_format_square(sq) for (sq, _, _) in thin_list[:5])
        max_def = _format_square(summary.get("max_defended"))
        return f"ThreatMap: thin={thin_count} [{squares}], max_def={max_def}"

    max_att = _format_square(summary.get("max_attacked"))
    max_def = _format_square(summary.get("max_defended"))
    return f"ThreatMap: thin=0, max_att={max_att}, max_def={max_def}"


def _attack_metrics(board: chess.Board) -> tuple[int, int, int, int]:
    cells_w = sum(
        1 for sq in chess.SQUARES if board.is_attacked_by(chess.WHITE, sq)
    )
    cells_b = sum(
        1 for sq in chess.SQUARES if board.is_attacked_by(chess.BLACK, sq)
    )

    pieces_w = 0
    pieces_b = 0
    for sq, piece in board.piece_map().items():
        if piece.color == chess.WHITE:
            if board.is_attacked_by(chess.BLACK, sq):
                pieces_w += 1
        else:
            if board.is_attacked_by(chess.WHITE, sq):
                pieces_b += 1

    return cells_w, cells_b, pieces_w, pieces_b


def _attack_leaders_text(board: chess.Board) -> str:
    data: Dict[chess.Color, Dict[chess.PieceType, int]] = {}
    for color in (chess.WHITE, chess.BLACK):
        unions: Dict[chess.PieceType, set[int]] = {
            chess.PAWN: set(),
            chess.KNIGHT: set(),
            chess.BISHOP: set(),
            chess.ROOK: set(),
            chess.QUEEN: set(),
            chess.KING: set(),
        }
        for square, piece in board.piece_map().items():
            if piece.color != color:
                continue
            unions[piece.piece_type] |= set(board.attacks(square))
        data[color] = {pt: len(squares) for pt, squares in unions.items()}

    def display_max_for(color: chess.Color) -> str:
        counts = data.get(color, {})
        if not counts:
            return "—"

        def display_value(piece_type: chess.PieceType) -> int:
            count = counts.get(piece_type, 0)
            return min(count, 8) if piece_type == chess.KING else count

        max_value = max(display_value(pt) for pt in counts)
        if max_value == 0:
            return "—"

        leaders = [
            pt for pt in counts if display_value(pt) == max_value
        ]
        names = ", ".join(_PIECE_NAME[pt] for pt in sorted(leaders))
        return f"{names}({max_value})"

    white_text = display_max_for(chess.WHITE)
    black_text = display_max_for(chess.BLACK)
    return f"Attack leaders: W={white_text} | B={black_text}"


def _king_coeff_text(board: chess.Board) -> str:
    def value_for(color: chess.Color) -> str:
        base = (
            8 * len(board.pieces(chess.PAWN, color))
            + 2 * len(board.pieces(chess.BISHOP, color))
            + 2 * len(board.pieces(chess.KNIGHT, color))
            + 2 * len(board.pieces(chess.ROOK, color))
            + len(board.pieces(chess.QUEEN, color))
        )
        modifier = 0.85 if not board.pieces(chess.QUEEN, not color) else 1.0
        value = int(base * modifier)
        return f"{value} (m={modifier:.2f})"

    white_val = value_for(chess.WHITE)
    black_val = value_for(chess.BLACK)
    return f"King coeff: W={white_val} | B={black_val}"


def build_sidebar_metrics(
    board: chess.Board, threat_maps: Dict[chess.Color, ThreatMap] | None = None
) -> List[str]:
    """Return formatted metrics describing *board* state."""

    metrics: List[str] = []
    metrics.append(_threat_map_summary(board, threat_maps))

    cells_w, cells_b, pieces_w, pieces_b = _attack_metrics(board)
    metrics.append(
        "Attacks: cells W={cw}, B={cb} | pieces under attack W={pw}, B={pb}".format(
            cw=cells_w, cb=cells_b, pw=pieces_w, pb=pieces_b
        )
    )

    metrics.append(_attack_leaders_text(board))
    metrics.append(_king_coeff_text(board))
    return metrics
