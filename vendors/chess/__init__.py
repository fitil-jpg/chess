"""Stub module for the optional :mod:`python-chess` dependency.

This repository avoids bundling heavy third‑party libraries.  When the
real ``python-chess`` package is unavailable, importing this stub allows the
test suite to gracefully skip any tests that depend on it.

Accessing any attribute of this module triggers a ``pytest.skip`` so that
tests using :mod:`chess` are reported as skipped rather than failing with an
``ImportError`` or ``AttributeError``.

Outside of ``pytest`` (for example, when running project scripts manually),
attempting to use this stub will raise ``ImportError`` to clearly signal the
missing dependency.
"""

from __future__ import annotations

import os
import inspect

try:  # pragma: no cover - pytest may not be installed outside tests
    import pytest  # type: ignore
except Exception:  # pragma: no cover - outside of pytest
    pytest = None  # type: ignore


def _running_under_pytest() -> bool:
    """Return ``True`` when code is executed within a pytest run."""
    if pytest is None:  # pragma: no cover - outside of pytest
        return False
    # Inspect the call stack for frames originating from ``_pytest`` modules,
    # which indicates that pytest is orchestrating execution.
    return any(frame.filename and "_pytest" in frame.filename for frame in inspect.stack())


def __getattr__(name: str):  # pragma: no cover - executed only when missing dep
    """On attribute access, skip dependent tests or raise ``ImportError``."""
    if _running_under_pytest():
        pytest.skip("python-chess not installed", allow_module_level=True)
    raise ImportError("python-chess is required for this feature")


__all__: list[str] = []
__version__ = "0.0.0"

