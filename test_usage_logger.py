import importlib
import builtins
import sys
import types


def test_record_usage_posix(tmp_path, monkeypatch):
    import utils.usage_logger as usage_logger
    ul = importlib.reload(usage_logger)
    monkeypatch.setattr(ul, "STATS_PATH", tmp_path / "usage_counts.json")
    ul.record_usage("foo")
    ul.record_usage("foo")
    assert ul.read_usage() == {"foo": 2}


def test_record_usage_windows_fallback(tmp_path, monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ("fcntl", "portalocker"):
            raise ImportError()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "fcntl", raising=False)
    monkeypatch.delitem(sys.modules, "portalocker", raising=False)

    dummy_msvcrt = types.SimpleNamespace(
        LK_LOCK=1,
        LK_RLCK=2,
        LK_UNLCK=0,
        locking=lambda fd, flag, length: None,
    )
    monkeypatch.setitem(sys.modules, "msvcrt", dummy_msvcrt)

    import utils.usage_logger as usage_logger
    ul = importlib.reload(usage_logger)
    monkeypatch.setattr(ul, "STATS_PATH", tmp_path / "usage_counts.json")
    ul.record_usage("bar")
    assert ul.read_usage() == {"bar": 1}


