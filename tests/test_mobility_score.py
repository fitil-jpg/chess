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
