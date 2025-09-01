from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from collections import Counter
from typing import Any, Iterable, Mapping, Dict


def aggregate_module_usage(runs: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    """Aggregate module usage counts across *runs*.

    Each run dictionary is expected to provide ``modules_w`` and ``modules_b``
    lists containing module names for White and Black.  The function iterates
    over all runs, counting how many times each module name appears across both
    colours.

    Parameters
    ----------
    runs:
        Iterable of run dictionaries as returned by :func:`utils.load_runs`.

    Returns
    -------
    Dict[str, int]
        Mapping of module name to total occurrence count across all runs.
    """
    counter: Counter[str] = Counter()
    for run in runs:
        for key in ("modules_w", "modules_b"):
            modules = run.get(key, [])
            counter.update(m for m in modules if isinstance(m, str))
    return dict(counter)