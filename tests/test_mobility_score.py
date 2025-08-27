import chess
from core.evaluator import Evaluator

def test_mobility_score_recorded():
    board = chess.Board()
    evaluator = Evaluator(board)
    white, black = evaluator.mobility(board)
    metrics = evaluator.compute_final_metrics()
    assert metrics['white_mobility'] == white
    assert metrics['black_mobility'] == black
    assert metrics['mobility_score'] == white - black


def test_mobility_handles_iterator_without_count():
    class DummyBoard(chess.Board):
        @property  # type: ignore[override]
        def legal_moves(self):
            return iter(super().legal_moves)

    board = DummyBoard()
    evaluator = Evaluator(board)
    white, black = evaluator.mobility(board)
    assert white >= 0 and black >= 0


def test_per_piece_mobility_flags():
    board = chess.Board()
    board.clear()
    board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.A2, chess.Piece(chess.PAWN, chess.WHITE))
    board.set_piece_at(chess.A3, chess.Piece(chess.PAWN, chess.BLACK))
    evaluator = Evaluator(board)
    evaluator.mobility(board)
    pawn_stats = evaluator.mobility_stats['white']['pieces'][chess.A2]
    assert pawn_stats['mobility'] == 0
    assert pawn_stats['blocked'] is True
    assert pawn_stats['capturable'] is True


def test_king_status_checkmate_and_stalemate():
    # Checkmate scenario
    mate = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    evaluator = Evaluator(mate)
    evaluator.mobility(mate)
    ksq = mate.king(chess.BLACK)
    status = evaluator.mobility_stats['black']['pieces'][ksq]['status']
    assert status == 'checkmated'

    # Stalemate scenario
    stale = chess.Board("7k/5Q2/7K/8/8/8/8/8 b - - 0 1")
    evaluator = Evaluator(stale)
    evaluator.mobility(stale)
    ksq = stale.king(chess.BLACK)
    status = evaluator.mobility_stats['black']['pieces'][ksq]['status']
    assert status == 'stalemated'
