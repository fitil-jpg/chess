"""Minimal rpy2 package initialiser for vendored tests.

The vendored copy of rpy2 only includes the submodules required for the test
suite.  Providing a ``__version__`` attribute keeps ``pytest.importorskip``
checks satisfied without installing the full dependency.
"""

__all__ = []
__version__ = "0.0.0"
