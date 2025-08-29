"""Stub for :mod:`chess.pgn` used in tests.

When the real `python-chess` package is unavailable, importing this module
within a pytest run will mark dependent tests as skipped.  Outside of pytest
it raises ``ImportError`` to clearly signal the missing dependency.
"""
from __future__ import annotations

import inspect

try:  # pragma: no cover - pytest may not be installed
    import pytest  # type: ignore
except Exception:  # pragma: no cover - outside of tests
    pytest = None  # type: ignore

if pytest is not None and any("_pytest" in frame.filename for frame in inspect.stack()):
    pytest.skip("python-chess not installed", allow_module_level=True)
else:  # pragma: no cover - executed outside of pytest
    raise ImportError("python-chess is required")
