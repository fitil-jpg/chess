import sys
from pathlib import Path

import pytest

# Ensure the vendored packages directory is available on PYTHONPATH.
VENDOR_DIR = Path(__file__).resolve().parent.parent / "vendors"
if str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

MODULES = ["python_chess", "torch", "rpy2", "matplotlib"]

@pytest.mark.parametrize("module_name", MODULES)
def test_vendor_imports(module_name):
    module = pytest.importorskip(module_name)
    version = getattr(module, "__version__", "")
    assert version, f"{module_name} failed to provide a __version__"
