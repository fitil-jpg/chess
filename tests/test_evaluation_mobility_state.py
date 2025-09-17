import chess

from evaluation import mobility_score


def snapshot_board_state(board: chess.Board) -> dict:
    """Capture key elements of the board state for comparison."""
    return {
        "fen": board.fen(),
        "turn": board.turn,
        "castling_rights": board.castling_rights,
        "ep_square": board.ep_square,
        "halfmove_clock": board.halfmove_clock,
        "fullmove_number": board.fullmove_number,
        "has_legal_en_passant": board.has_legal_en_passant(),
    }


def test_mobility_score_preserves_castling_rights():
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 5 17")
    before = snapshot_board_state(board)

    mobility_score(board)

    after = snapshot_board_state(board)
    assert after == before, "Board state changed after mobility_score with castling rights"


def test_mobility_score_preserves_en_passant_state():
    board = chess.Board()
    board.push_san("e4")
    board.push_san("d5")
    board.push_san("exd5")
    board.push_san("c5")
    before = snapshot_board_state(board)

    mobility_score(board)

    after = snapshot_board_state(board)
    assert after == before, "Board state changed after mobility_score with en passant rights"
