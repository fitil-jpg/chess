import subprocess
import sys
from pathlib import Path
import importlib.util

import pytest


def test_stub_raises_importerror_outside_pytest():
    spec = importlib.util.find_spec("chess")
    if spec and spec.origin:
        vendors_dir = Path(__file__).resolve().parent.parent / "vendors"
        chess_path = Path(spec.origin).resolve()
        try:
            chess_path.relative_to(vendors_dir)
        except ValueError:
            pytest.skip("real python-chess installed")
    code = (
        "import sys\n"
        "sys.path.append('vendors')\n"
        "import chess\n"
        "try:\n"
        "    chess.A1\n"
        "except ImportError:\n"
        "    sys.exit(0)\n"
        "else:\n"
        "    sys.exit(1)\n"
    )
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "-c", code], cwd=root)
    assert result.returncode == 0
