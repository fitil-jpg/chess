"""Test package initializer.

Ensures the project root and vendored libraries are importable when test
modules are executed as scripts.
"""

import os
import sys

# Make project root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure vendored third-party packages
import vendors.setup_path  # noqa: F401

