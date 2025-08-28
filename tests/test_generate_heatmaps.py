import sys
import types
import importlib.util
from pathlib import Path
import pytest


def test_generate_heatmaps_rscript_missing(monkeypatch, tmp_path):
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

    with pytest.raises(RuntimeError, match="Rscript not found; install R to generate heatmaps"):
        integration.generate_heatmaps([], out_dir=str(tmp_path))

