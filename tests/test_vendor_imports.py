import pytest

MODULES = ["chess", "torch", "rpy2", "matplotlib"]

@pytest.mark.parametrize("module_name", MODULES)
def test_dependency_imports(module_name):
    module = pytest.importorskip(module_name)
    version = getattr(module, "__version__", "")
    assert version, f"{module_name} failed to provide a __version__"
