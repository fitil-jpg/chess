from core.board import Board
from core.piece import Pawn, Knight
from core.board_analyzer import BoardAnalyzer
from core.evaluation_tuner import EvaluationTuner
from core.agent_evaluator import AgentEvaluator
from core.metrics import BoardMetrics


def test_agent_evaluator():
    print("\n=== 🧪 Running AgentEvaluator test ===")
    board = Board()
    board.place_piece(Pawn('white', 'e2'))
    board.place_piece(Knight('white', 'g1'))
    board.place_piece(Pawn('black', 'e7'))

    analyzer = BoardAnalyzer(board)
    tuner = EvaluationTuner()
    agent = AgentEvaluator(tuner)

    score = agent.evaluate(board, analyzer)
    print("Board position:")
    print(board)  # If your Board has __str__, else remove
    print("Оцінка позиції агентом:", score)

    assert isinstance(score, float), "Score is not a float!"
    print("✅ AgentEvaluator test passed.")


def test_board_metrics():
    print("\n=== 🧪 Running BoardMetrics test ===")
    board = Board()
    board.place_piece(Pawn('white', 'e2'))
    board.place_piece(Knight('white', 'g1'))
    board.place_piece(Pawn('black', 'e7'))

    analyzer = BoardAnalyzer(board)
    metrics = BoardMetrics()
    metrics.update_from_board(board, analyzer)

    result = metrics.get_metrics()
    print("Board position:")
    print(board)  # If your Board has __str__, else remove
    print("Оцінка метрик (детально):")
    for k, v in result.items():
        print(f"  {k}: {v}")

    assert isinstance(result, dict), "Metrics result is not a dict!"
    assert 'material_balance' in result, "No material_balance key found!"
    print("✅ BoardMetrics test passed.")


if __name__ == "__main__":
    test_agent_evaluator()
    test_board_metrics()
