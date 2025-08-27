import chess

from chess_ai.hybrid_orchestrator import HybridOrchestrator


# python-chess versions prior to 1.12 lack ``transposition_key``.  The vendored
# version used in this repository may fall into this category, so provide a
# fallback for compatibility with the alpha-beta search used by the orchestrator.
if not hasattr(chess.Board, "transposition_key"):  # pragma: no cover - version dependent
    chess.Board.transposition_key = chess.Board._transposition_key  # type: ignore[attr-defined]


def test_hybrid_orchestrator_returns_move_and_diag():
    board = chess.Board()
    orch = HybridOrchestrator(chess.WHITE, mcts_simulations=8, ab_depth=2, top_k=2)
    move, diag = orch.choose_move(board)
    assert move in board.legal_moves
    assert isinstance(diag, dict)
    assert diag["candidates"] and "chosen" in diag
