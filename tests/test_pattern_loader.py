from pathlib import Path

import chess

from core.pattern_loader import PatternResponder


def test_pattern_match() -> None:
    responder = PatternResponder.from_file(Path("configs/patterns.json"))
    board = chess.Board()
    board.push_san("e4")
    assert responder.match(board) == "e7e5"
    board.push_san("e5")
    assert responder.match(board) == "g1f3"
