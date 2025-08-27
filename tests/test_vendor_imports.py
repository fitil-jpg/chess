import pytest

# Rely on the environment's installed packages without adjusting ``sys.path``.
MODULES = ["chess", "torch", "matplotlib"]


@pytest.mark.parametrize("module_name", MODULES)
def test_dependency_imports(module_name):
    module = pytest.importorskip(module_name)
    version = getattr(module, "__version__", "")
    assert version, f"{module_name} failed to provide a __version__"
