"""Pytest configuration for the test suite.

This file ensures that vendored dependencies placed in ``vendors/`` are
discoverable when tests import them. The directory is appended to
``sys.path`` **before** attempting any imports so that lightweight stub
packages can satisfy optional dependencies like ``chess`` or ``torch``.
"""

from pathlib import Path
import sys

import pytest

# Add the top-level ``vendors`` directory to ``sys.path`` if it exists.
VENDOR_PATH = Path(__file__).resolve().parents[1] / "vendors"
if VENDOR_PATH.exists():
    sys.path.append(str(VENDOR_PATH))

try:  # pragma: no cover - handled in fixtures
    import chess
except Exception:  # ImportError or partial stubs lacking attributes
    chess = None


@pytest.fixture(scope="module")
def evaluator():
    """Shared evaluator instance reused across tests."""
    if chess is None:
        pytest.skip("python-chess not installed")
    from core.evaluator import Evaluator
    return Evaluator(chess.Board())


@pytest.fixture
def context():
    """Minimal game context with neutral metrics."""
    from utils import GameContext
    return GameContext()
