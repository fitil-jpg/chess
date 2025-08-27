from vendors import setup_path  # noqa: F401

from core.board import Board
from core.piece import Pawn, Knight
from core.board_analyzer import BoardAnalyzer
from core.evaluation_tuner import EvaluationTuner
from core.agent_evaluator import AgentEvaluator


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
