def test_agent_evaluator():
    board = Board()
    board.place_piece(Pawn('white', 'e2'))
    board.place_piece(Knight('white', 'g1'))
    board.place_piece(Pawn('black', 'e7'))

    analyzer = BoardAnalyzer(board)
    tuner = EvaluationTuner()
    agent = AgentEvaluator(tuner)

    score = agent.evaluate(board, analyzer)
    print("Оцінка позиції агентом:", score)
    assert isinstance(score, float)