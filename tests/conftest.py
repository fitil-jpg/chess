import pytest

try:
    import chess
except ImportError:  # pragma: no cover - handled in fixtures
    chess = None

from utils import GameContext

if chess is not None:
    from core.evaluator import Evaluator


@pytest.fixture(scope="module")
def evaluator():
    """Shared evaluator instance reused across tests."""
    if chess is None:
        pytest.skip("python-chess not installed")
    return Evaluator(chess.Board())


@pytest.fixture
def context():
    """Minimal game context with neutral metrics."""
    return GameContext()
