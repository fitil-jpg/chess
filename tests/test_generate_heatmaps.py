import logging
import sys
import types
import importlib.util
from pathlib import Path
import pytest

logger = logging.getLogger(__name__)
pytestmark = pytest.mark.utils


@pytest.mark.parametrize(
    "use_wolfram,missing",
    [(False, "Rscript"), (True, "wolframscript")],
)
def test_generate_heatmaps_script_missing(monkeypatch, tmp_path, use_wolfram, missing):
    dummy_chess = types.SimpleNamespace(Board=object)
    monkeypatch.setitem(sys.modules, "chess", dummy_chess)

    spec = importlib.util.spec_from_file_location(
        "integration", Path(__file__).resolve().parents[1] / "utils" / "integration.py"
    )
    integration = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(integration)

    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(integration.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match=f"{missing} not found"):
        integration.generate_heatmaps([], out_dir=str(tmp_path), use_wolfram=use_wolfram)

