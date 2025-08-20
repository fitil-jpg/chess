import importlib
import importlib.util

import chess
import pytest

from chess_ai.hybrid_bot.mcts import BatchMCTS
from chess_ai.hybrid_bot.alpha_beta import search as ab_search

# python-chess versions prior to 1.12 lack ``transposition_key``.
if not hasattr(chess.Board, "transposition_key"):  # pragma: no cover - version dependent
    chess.Board.transposition_key = chess.Board._transposition_key  # type: ignore[attr-defined]


def _play_with_orchestrator(monkeypatch, use_r: bool) -> None:
    if use_r:
        monkeypatch.setenv("CHESS_USE_R", "1")
    else:
        monkeypatch.delenv("CHESS_USE_R", raising=False)
    import chess_ai.hybrid_bot.orchestrator as orch
    importlib.reload(orch)

    board = chess.Board()
    white = orch.HybridOrchestrator(chess.WHITE, mcts_simulations=8, ab_depth=2)
    black = orch.HybridOrchestrator(chess.BLACK, mcts_simulations=8, ab_depth=2)
    for _ in range(4):
        current = white if board.turn == chess.WHITE else black
        move, _ = current.choose_move(board)
        assert move in board.legal_moves
        board.push(move)


def test_mcts_returns_legal_moves():
    board = chess.Board()
    mcts = BatchMCTS()
    for _ in range(4):
        move, _ = mcts.search(board, n_simulations=8)
        assert move in board.legal_moves
        board.push(move)


def test_alpha_beta_returns_legal_moves():
    board = chess.Board()
    for _ in range(4):
        _, move = ab_search(board, 2)
        assert move in board.legal_moves
        board.push(move)


def test_hybrid_orchestrator_returns_legal_moves(monkeypatch):
    _play_with_orchestrator(monkeypatch, use_r=False)


@pytest.mark.skipif(
    importlib.util.find_spec("rpy2") is None,
    reason="rpy2 or R is not available",
)
def test_hybrid_orchestrator_with_r_returns_legal_moves(monkeypatch):
    _play_with_orchestrator(monkeypatch, use_r=True)
