import chess
import pytest

from core.evaluator import Evaluator
from utils import GameContext


@pytest.fixture(scope="module")
def evaluator():
    """Shared evaluator instance reused across tests."""
    return Evaluator(chess.Board())


@pytest.fixture
def context():
    """Minimal game context with neutral metrics."""
    return GameContext(material_diff=0, mobility=0, king_safety=0)
