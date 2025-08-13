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
