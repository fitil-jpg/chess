"""Visualization helpers for the hybrid orchestrator."""

from __future__ import annotations

from typing import Any, Mapping, Sequence, Tuple


def plot_orchestrator_diag(
    diag: Mapping[str, Any],
    title: str | None = None,
    save_path: str | None = None,
) -> Tuple["Figure", Sequence["Axes"]]:
    """Plot diagnostic information returned by :class:`HybridOrchestrator`.

    Parameters
    ----------
    diag:
        Dictionary produced by :meth:`HybridOrchestrator.choose_move` containing
        a ``"candidates"`` list and ``"chosen"`` move.
    title:
        Optional figure title.
    save_path:
        If provided, the figure is saved to this path using
        :func:`matplotlib.figure.Figure.savefig`.

    Returns
    -------
    ``(fig, axes)``
        Created matplotlib figure and axes.
    """

    import matplotlib.pyplot as plt  # local import to avoid heavy dependency

    candidates = diag.get("candidates", [])
    moves = [c.get("move", "?") for c in candidates]
    mcts_vals = [c.get("mcts", 0.0) for c in candidates]
    ab_vals = [c.get("ab", 0.0) for c in candidates]
    mixed_vals = [c.get("mixed", 0.0) for c in candidates]
    chosen = diag.get("chosen")

    # Highlight the chosen move.
    colors = ["tab:orange" if m == chosen else "tab:blue" for m in moves]

    x = list(range(len(moves)))

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    axes[0].bar(x, mcts_vals, color=colors)
    axes[0].set_title("MCTS visits")
    axes[0].set_ylabel("value")

    axes[1].bar(x, ab_vals, color=colors)
    axes[1].set_title("AB score")

    axes[2].bar(x, mixed_vals, color=colors)
    axes[2].set_title("Mixed value")

    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(moves, rotation=45)

    if title:
        fig.suptitle(title)

    fig.tight_layout()

    if save_path is not None:
        fig.savefig(save_path, bbox_inches="tight")

    return fig, axes


__all__ = ["plot_orchestrator_diag"]

