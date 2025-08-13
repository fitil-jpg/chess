import chess

from chess_ai.decision_engine import DecisionEngine


def test_capture_beats_perpetual_check():
    """Перевіряємо, що захоплення ладді переважає серію шахів."""
    board = chess.Board("r3n1k1/8/8/3Q4/8/8/8/5K2 w - - 0 1")
    engine = DecisionEngine()
    best = engine.choose_best_move(board)
    assert best == chess.Move.from_uci("d5a8"), "Engine should capture the rook"


def test_quiescence_avoids_hanging_capture():
    """Quiescence search should prevent obviously losing captures."""
    board = chess.Board("r5k1/8/8/p7/Q7/8/8/6K1 w - - 0 1")
    engine = DecisionEngine()
    best = engine.choose_best_move(board)
    assert best != chess.Move.from_uci("a4a5"), "Engine should avoid losing the queen"

