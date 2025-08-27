"""Test package initialiser.

Ensures the project root is importable when the test modules are executed as
scripts.  This mirrors the behaviour of common test runners and keeps the
examples self-contained.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

