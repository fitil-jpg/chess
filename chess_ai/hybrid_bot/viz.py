"""Visualization helpers for the hybrid orchestrator."""

from __future__ import annotations

from typing import Mapping


def plot_orchestrator_diag(stats: Mapping[str, float]):
    """Plot simple diagnostic bars using :mod:`matplotlib`.

    ``stats`` maps labels to numeric scores.  The function returns the created
    ``(fig, ax)`` tuple so callers may further adjust or save the figure.
    ``matplotlib`` is imported lazily to keep the module lightweight.
    """
    import matplotlib.pyplot as plt  # local import to avoid heavy dependency

    labels = list(stats.keys())
    values = list(stats.values())
    fig, ax = plt.subplots()
    ax.bar(labels, values)
    ax.set_ylabel("score")
    ax.set_title("Hybrid orchestrator diagnostics")
    return fig, ax

