class AgentEvaluator:
    def __init__(self, tuner):
        self.tuner = tuner

    def evaluate(self, board, analyzer):
        metrics = BoardMetrics()
        metrics.update_from_board(board, analyzer)
        phase = GamePhaseDetector.detect(board)
        self.tuner.adjust_weights(phase)
        return self.tuner.evaluate_position(metrics.get_metrics())