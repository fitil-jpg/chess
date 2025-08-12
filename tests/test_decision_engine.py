import chess

from chess_ai.decision_engine import DecisionEngine


def test_capture_beats_perpetual_check():
    """Перевіряємо, що захоплення ладді переважає серію шахів."""
    board = chess.Board("r3n1k1/8/8/3Q4/8/8/8/5K2 w - - 0 1")
    engine = DecisionEngine()
    best = engine.choose_best_move(board)
    assert best == chess.Move.from_uci("d5a8"), "Engine should capture the rook"

