# evaluation.py
from typing import Optional

import chess
from pst_loader import effective_pst_for_piece, game_phase_from_board
from pst_tables import PIECE_VALUES

MATE_SCORE = 100_000

def material_score(board: chess.Board) -> int:
    score = 0
    for piece_type in range(1, 7):
        score += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
    return score

def pst_score(board: chess.Board) -> int:
    """Бонуси/штрафи з таблиць. Для чорних дзеркалим квадрат."""
    score = 0
    phase = game_phase_from_board(board)
    for piece_type in range(1, 7):
        table = effective_pst_for_piece(piece_type, phase=phase)
        for sq in board.pieces(piece_type, chess.WHITE):
            score += table[sq]
        for sq in board.pieces(piece_type, chess.BLACK):
            score -= table[chess.square_mirror(sq)]
    return score

def mobility_score(board: chess.Board) -> int:
    """Проста мобільність: #ходів білих - #ходів чорних з поточної позиції."""
    if board.is_game_over():
        return 0

    # Порахуємо к-ть легальних ходів для кожної сторони, не змінюючи позицію.
    white_board = board.copy(stack=False)
    white_board.turn = chess.WHITE
    white_moves = sum(1 for _ in white_board.legal_moves)

    black_board = board.copy(stack=False)
    black_board.turn = chess.BLACK
    black_moves = sum(1 for _ in black_board.legal_moves)

    return (white_moves - black_moves) * 2  # невелика вага

def attacked_squares_metrics(board: chess.Board) -> dict:
    """Незалежна метрика: скільки клітин атакують білі/чорні (прибл.)."""
    def count_attacks(color: chess.Color) -> int:
        total = 0
        for sq in chess.SQUARES:
            if board.is_attacked_by(color, sq):
                total += 1
        return total

    white_attacks = count_attacks(chess.WHITE)
    black_attacks = count_attacks(chess.BLACK)

    return {
        "white_attacks": white_attacks,
        "black_attacks": black_attacks,
        "delta_attacks": white_attacks - black_attacks,
    }

def _terminal_score(board: chess.Board) -> Optional[int]:
    """Return a terminal score if the position is terminal."""

    if board.is_checkmate():
        score = MATE_SCORE if board.turn == chess.BLACK else -MATE_SCORE
        return score

    draw_detectors = [
        board.is_stalemate,
        getattr(board, "is_insufficient_material", lambda: False),
        getattr(board, "is_seventyfive_moves", lambda: False),
        getattr(board, "is_fivefold_repetition", lambda: False),
        board.is_repetition,
    ]

    for detector in draw_detectors:
        try:
            if detector():
                return 0
        except TypeError:
            # ``board.is_repetition`` accepts an optional count parameter in
            # some python-chess versions.  Retry with the default claim value.
            if detector is board.is_repetition and detector(3):
                return 0

    return None


def _evaluation_components(board: chess.Board) -> tuple[int, dict]:
    mat = material_score(board)
    pst = pst_score(board)
    mob = mobility_score(board)
    atk = attacked_squares_metrics(board)
    total = mat + pst + mob + atk["delta_attacks"]  # delta_attacks – маленька добавка

    details = {
        "material": mat,
        "pst": pst,
        "mobility": mob,
        "attacks_white": atk["white_attacks"],
        "attacks_black": atk["black_attacks"],
        "delta_attacks": atk["delta_attacks"],
        "total": total,
    }

    return total, details


def evaluate(board: chess.Board) -> tuple[int, dict]:
    """Повертає (оцінка з точки зору БІЛИХ, деталi)."""

    terminal_score = _terminal_score(board)
    total, details = _evaluation_components(board)

    if terminal_score is not None:
        details["total"] = terminal_score
        return terminal_score, details

    return total, details
