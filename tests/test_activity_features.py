import chess

from chess_ai.evaluator import Evaluator


def test_activity_features_present():
    """Після ходу повинні зʼявлятися ознаки активності та відкритої лінії."""
    board = chess.Board("4k3/8/8/8/8/8/4R3/K7 w - - 0 1")
    evaluator = Evaluator(board)
    move = chess.Move.from_uci("e2e7")

    features = evaluator.extract_features(move)

    assert "active_piece" in features
    assert "open_file_to_king" in features
    assert features["active_piece"] > 0
    assert features["open_file_to_king"] is True

