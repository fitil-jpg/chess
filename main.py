# main.py — запуск проєкту

from core.board import Board
from core.piece import Pawn, Knight
from core.board_analyzer import BoardAnalyzer
from core.metrics import BoardMetrics, EvaluationTuner
from core.evaluator import AgentEvaluator
from core.phase import GamePhaseDetector
from utils.logger import GameLogger
from ui.interface import print_debug_view

# 1. Ініціалізація дошки та фігур
board = Board()
board.place_piece(Pawn('white', 'e2'))
board.place_piece(Knight('white', 'g1'))
board.place_piece(Pawn('black', 'e7'))

# 2. Запуск аналітики
analyzer = BoardAnalyzer(board)
tuner = EvaluationTuner()
evaluator = AgentEvaluator(tuner)
logger = GameLogger()

# 3. Оцінка позиції
score = evaluator.evaluate(board, analyzer)
metrics = BoardMetrics()
metrics.update_from_board(board, analyzer)

# 4. Виведення
logger.record_move("e2e4", "white", score, GamePhaseDetector.detect(board))
print_debug_view(board, score, metrics.get_metrics(), move="e2e4", phase="opening")
