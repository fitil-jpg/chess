"""Test package initialiser.

Ensures the project root is importable when the test modules are executed as
scripts and configures vendored third‑party libraries.
"""

import os
import sys

# Make project root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Add vendored packages to sys.path
import vendors.setup_path  # noqa: F401
