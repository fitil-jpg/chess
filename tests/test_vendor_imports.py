import pytest

MODULES = ["torch", "matplotlib", "rpy2"]

@pytest.mark.parametrize("module_name", MODULES)
def test_vendor_imports(module_name):
    module = pytest.importorskip(module_name)
    version = getattr(module, "__version__", "")
    assert version, f"{module_name} failed to provide a __version__"
