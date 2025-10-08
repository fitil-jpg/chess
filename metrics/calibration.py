"""Calibration utilities for normalising bot scores and estimating win probability.

This module provides:
- Common scale conversions between centipawn evaluations and win probability
- Simple temperature scaling and Platt (logistic) calibration
- Expected Calibration Error (ECE) computation
- A lightweight reliability-curve helper that returns bin stats (and an
  optional plotting function if matplotlib is available)

The functions are dependency-light. Plotting only occurs if matplotlib is
installed; otherwise, the numeric bin summary is returned for external use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple
import math


# ---------------------------------------------------------------------------
# Scale conversions
# ---------------------------------------------------------------------------

def centipawn_to_winprob(cp: float, *, slope: float = 1.0 / 120.0) -> float:
    """Convert a centipawn score (from side-to-move perspective) to win prob.

    Uses a logistic mapping p = 1 / (1 + exp(-slope * cp)). The default slope
    is a conservative setting; tune empirically using self-play logs.
    """

    # Clamp extreme values for numerical stability
    x = max(min(cp, 10000.0), -10000.0)
    return 1.0 / (1.0 + math.exp(-slope * x))


def winprob_to_centipawn(p: float, *, slope: float = 1.0 / 120.0) -> float:
    """Inverse of :func:`centipawn_to_winprob` with the same slope."""

    eps = 1e-12
    p = min(max(p, eps), 1.0 - eps)
    return math.log(p / (1.0 - p)) / slope


# ---------------------------------------------------------------------------
# Parametric calibrators
# ---------------------------------------------------------------------------

@dataclass
class TemperatureCalibrator:
    """Temperature scaling for raw logits (or log-odds).

    Given raw scores ``z``, the calibrated probability is
    ``sigmoid(z / temperature)``.
    """

    temperature: float = 1.0

    def predict_proba(self, z: Iterable[float]) -> List[float]:
        t = max(self.temperature, 1e-6)
        return [1.0 / (1.0 + math.exp(-float(v) / t)) for v in z]


@dataclass
class PlattCalibrator:
    """Platt scaling: sigmoid(a * z + b), parameters learned via logistic loss.

    This is a light-weight implementation using a few steps of gradient descent
    for stability. For production, consider scikit-learn's implementation.
    """

    a: float = 1.0
    b: float = 0.0

    def fit(self, z: Iterable[float], y: Iterable[int], *, lr: float = 0.01, steps: int = 200) -> "PlattCalibrator":
        zs = [float(v) for v in z]
        ys = [int(t) for t in y]
        a, b = float(self.a), float(self.b)
        for _ in range(max(1, steps)):
            da = 0.0
            db = 0.0
            for zi, yi in zip(zs, ys):
                p = 1.0 / (1.0 + math.exp(-(a * zi + b)))
                grad = (p - yi)
                da += grad * zi
                db += grad
            n = max(1, len(zs))
            a -= lr * da / n
            b -= lr * db / n
        self.a, self.b = a, b
        return self

    def predict_proba(self, z: Iterable[float]) -> List[float]:
        a, b = self.a, self.b
        return [1.0 / (1.0 + math.exp(-(a * float(v) + b))) for v in z]


# ---------------------------------------------------------------------------
# Calibration metrics
# ---------------------------------------------------------------------------

def expected_calibration_error(
    probs: Iterable[float],
    labels: Iterable[int],
    *,
    num_bins: int = 10,
) -> float:
    """Compute Expected Calibration Error (ECE) with equal-width bins.

    ECE = sum_b (n_b / N) * |acc_b - conf_b|
    where ``acc_b`` is the average accuracy in bin b and ``conf_b`` is the
    average predicted probability in bin b.
    """

    buckets: List[List[Tuple[float, int]]] = [[] for _ in range(num_bins)]
    for p, y in zip(probs, labels):
        p = float(min(max(p, 0.0), 1.0))
        idx = min(num_bins - 1, int(p * num_bins))
        buckets[idx].append((p, int(y)))

    total = sum(len(b) for b in buckets) or 1
    ece = 0.0
    for b in buckets:
        if not b:
            continue
        n = len(b)
        acc = sum(y for _, y in b) / n
        conf = sum(p for p, _ in b) / n
        ece += (n / total) * abs(acc - conf)
    return float(ece)


def reliability_curve(
    probs: Iterable[float],
    labels: Iterable[int],
    *,
    num_bins: int = 10,
):
    """Return bin centers, accuracies, confidences, counts for reliability diagram.

    This function does not plot by default; it returns numerical arrays for
    external plotting. If matplotlib is available, call
    :func:`plot_reliability_diagram` to render a chart from these arrays.
    """

    buckets: List[List[Tuple[float, int]]] = [[] for _ in range(num_bins)]
    for p, y in zip(probs, labels):
        p = float(min(max(p, 0.0), 1.0))
        idx = min(num_bins - 1, int(p * num_bins))
        buckets[idx].append((p, int(y)))

    centers: List[float] = []
    accs: List[float] = []
    confs: List[float] = []
    counts: List[int] = []

    for i, b in enumerate(buckets):
        lo = i / num_bins
        hi = (i + 1) / num_bins
        centers.append((lo + hi) / 2.0)
        if not b:
            accs.append(0.0)
            confs.append((lo + hi) / 2.0)
            counts.append(0)
            continue
        n = len(b)
        counts.append(n)
        accs.append(sum(y for _, y in b) / n)
        confs.append(sum(p for p, _ in b) / n)

    return centers, accs, confs, counts


def plot_reliability_diagram(
    probs: Iterable[float], labels: Iterable[int], *, num_bins: int = 10
):
    """Plot a reliability diagram if matplotlib is available.

    Returns the matplotlib figure or ``None`` if the dependency is missing.
    """

    try:  # Lazy import to keep core runtime light
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return None

    centers, accs, confs, counts = reliability_curve(probs, labels, num_bins=num_bins)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="perfect")
    ax.bar(centers, accs, width=1.0 / num_bins, alpha=0.6, label="accuracy")
    ax.plot(centers, confs, "o-", color="C1", label="confidence")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed accuracy")
    ax.set_title("Reliability diagram")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend()
    ax.grid(True, linestyle=":", linewidth=0.5)
    return fig


# ---------------------------------------------------------------------------
# Convenience helpers for bots
# ---------------------------------------------------------------------------

def aggregate_scores_to_winprob(scores: Iterable[float], *, slope: float = 1.0 / 120.0) -> float:
    """Aggregate multiple centipawn-like scores into a single win probability.

    This helper converts each score into a win probability and averages them.
    Callers can provide better aggregation (e.g., weighted by agent weights)
    upstream and then pass a single combined centipawn score here instead.
    """

    probs = [centipawn_to_winprob(s, slope=slope) for s in scores]
    if not probs:
        return 0.5
    return sum(probs) / len(probs)

