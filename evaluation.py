# evaluation.py
import chess
from pst_tables import PST_MG, PIECE_VALUES

def material_score(board: chess.Board) -> int:
    score = 0
    for piece_type in range(1, 7):
        score += len(board.pieces(piece_type, chess.WHITE)) * PIECE_VALUES[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * PIECE_VALUES[piece_type]
    return score

def pst_score(board: chess.Board) -> int:
    """Бонуси/штрафи з таблиць. Для чорних дзеркалим квадрат."""
    score = 0
    for piece_type in range(1, 7):
        table = PST_MG[piece_type]
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
    turn = board.turn
    board.turn = chess.WHITE
    white_moves = sum(1 for _ in board.legal_moves)
    board.turn = chess.BLACK
    black_moves = sum(1 for _ in board.legal_moves)
    board.turn = turn

    return (white_moves - black_moves) * 2  # невелика вага

def attacked_squares_metrics(board: chess.Board) -> dict:
    """Незалежна метрика: скільки клітин атакують білі/чорні (прибл.)."""
    def count_attacks(color: chess.Color) -> int:
        total = 0
        for sq in chess.SQUARES:
            if board.is_attacked_by(color, sq):
                total += 1
        return total

    return {
        "white_attacks": count_attacks(chess.WHITE),
        "black_attacks": count_attacks(chess.BLACK),
        "delta_attacks": count_attacks(chess.WHITE) - count_attacks(chess.BLACK),
    }

def evaluate(board: chess.Board) -> tuple[int, dict]:
    """Повертає (оцінка з точки зору БІЛИХ, деталi)."""
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
