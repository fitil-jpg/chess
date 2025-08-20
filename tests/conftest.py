import sys
from pathlib import Path

# ``vendors/`` contains all third-party libraries bundled with the project.
# Prepend it to ``sys.path`` so modules like ``PySide6`` can be imported
# without being globally installed.
vendor_root = Path(__file__).resolve().parents[1] / "vendors"
sys.path.insert(0, str(vendor_root))
assert sys.path[0] == str(vendor_root)

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
    return GameContext()
