from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass
import time
from typing import Optional


@dataclass
class ProfileStats:
    """Simple container tracking search profiling statistics."""

    nodes: int = 0
    cutoffs: int = 0
    tt_hits: int = 0
    lmr_reductions: int = 0
    start_time: float = 0.0
    elapsed: float = 0.0

    def reset(self) -> None:
        self.nodes = 0
        self.cutoffs = 0
        self.tt_hits = 0
        self.lmr_reductions = 0
        self.start_time = 0.0
        self.elapsed = 0.0

    def start(self) -> None:
        """Reset counters and start the timer."""
        self.reset()
        self.start_time = time.time()

    def stop(self) -> None:
        """Stop the timer."""
        if self.start_time:
            self.elapsed = time.time() - self.start_time

    # Convenience metrics -------------------------------------------------
    @property
    def nodes_per_sec(self) -> float:
        return self.nodes / self.elapsed if self.elapsed else 0.0

    @property
    def cutoff_pct(self) -> float:
        return (self.cutoffs / self.nodes * 100) if self.nodes else 0.0

    @property
    def lmr_pct(self) -> float:
        return (self.lmr_reductions / self.nodes * 100) if self.nodes else 0.0

    def summary(self) -> str:
        return (
            f"nodes={self.nodes} ({self.nodes_per_sec:.1f}/s), "
            f"cutoffs={self.cutoffs} ({self.cutoff_pct:.1f}%), "
            f"tt_hits={self.tt_hits}, "
            f"lmr={self.lmr_reductions} ({self.lmr_pct:.1f}%), "
            f"time={self.elapsed:.3f}s"
        )


STATS = ProfileStats()


def plot_profile_stats(stats: ProfileStats, filename: Optional[str] = None) -> None:
    """Visualise key metrics using matplotlib.

    If ``filename`` is provided the plot is saved to that path.  When
    matplotlib is not available the function simply returns without error.
    """
    try:  # import lazily to avoid mandatory dependency during tests
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:  # pragma: no cover - matplotlib may be unavailable
        return

    metrics = {
        "Nodes/s": stats.nodes_per_sec,
        "Cutoff %": stats.cutoff_pct,
        "LMR %": stats.lmr_pct,
    }

    fig, ax = plt.subplots()
    ax.bar(metrics.keys(), metrics.values())
    ax.set_ylabel("Value")
    ax.set_title("Search profile")
    fig.tight_layout()
    if filename:
        fig.savefig(filename)
    else:  # pragma: no cover - interactive display not used in tests
        plt.show()
    plt.close(fig)


__all__ = ["ProfileStats", "STATS", "plot_profile_stats"]