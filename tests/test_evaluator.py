from core.board import Board
from core.piece import Pawn, Knight
from core.board_analyzer import BoardAnalyzer
from core.evaluation_tuner import EvaluationTuner
from core.agent_evaluator import AgentEvaluator
from core.metrics import BoardMetrics


def test_agent_evaluator():
    board = Board()
    board.place_piece(Pawn("white", "e2"))
    board.place_piece(Knight("white", "g1"))
    board.place_piece(Pawn("black", "e7"))

    analyzer = BoardAnalyzer(board)
    tuner = EvaluationTuner()
    agent = AgentEvaluator(tuner)

    score = agent.evaluate(board, analyzer)

    assert isinstance(score, (int, float)), "Score is not numeric!"


def test_board_metrics():
    board = Board()
    board.place_piece(Pawn("white", "e2"))
    board.place_piece(Knight("white", "g1"))
    board.place_piece(Pawn("black", "e7"))

    analyzer = BoardAnalyzer(board)
    metrics = BoardMetrics()
    metrics.update_from_board(board, analyzer)

    result = metrics.get_metrics()

    assert isinstance(result, dict), "Metrics result is not a dict!"
    assert "material_balance" in result, "No material_balance key found!"


if __name__ == "__main__":
    test_agent_evaluator()
    test_board_metrics()
