import sys
from pathlib import Path

# Ensure vendored dependencies are importable by adding the ``vendors/chess``
# directory to ``sys.path`` before any other imports occur and verifying it is
# inserted ahead of other locations.
vendor_path = Path(__file__).resolve().parents[1] / "vendors" / "chess"
sys.path.insert(0, str(vendor_path))
assert sys.path[0] == str(vendor_path)

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
