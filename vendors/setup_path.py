"""Utilities for vendored dependencies.

Provides :func:`setup_path` to insert the ``vendors`` directory into
``sys.path`` so the vendored packages can be imported without being
installed globally.
"""

from __future__ import annotations

import os
import sys


def setup_path() -> None:
    """Add the vendored packages directory to ``sys.path``.

    This allows the repository's vendored third-party libraries to be
    imported as normal modules.
    """
    vendor_dir = os.path.dirname(__file__)
    if vendor_dir not in sys.path:
        sys.path.insert(0, vendor_dir)

setup_path()
