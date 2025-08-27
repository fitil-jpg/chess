import subprocess
import sys
from pathlib import Path


def test_stub_raises_importerror_outside_pytest():
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
