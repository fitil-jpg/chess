"""Test package initialiser.

Ensures the project root is importable when the test modules are executed as
scripts. Vendored third-party libraries are configured in ``tests/conftest.py``.
"""

import os
import sys

# Make project root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

