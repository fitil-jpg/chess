from __future__ import annotations

import time
from typing import Optional


class Deadline:
    """Helper to manage per-move time budgets based on time.monotonic().

    Create with a duration in seconds or an absolute ``until`` timestamp.
    """

    def __init__(self, *, seconds: Optional[float] = None, until: Optional[float] = None) -> None:
        if until is None and seconds is None:
            raise ValueError("Provide either seconds or until")
        self.start: float = time.monotonic()
        self.until: float = until if until is not None else self.start + float(seconds)  # type: ignore[arg-type]

    def time_left(self) -> float:
        return max(0.0, self.until - time.monotonic())

    def exceeded(self) -> bool:
        return time.monotonic() >= self.until

    def remaining_fraction(self, min_denom: float = 1e-9) -> float:
        denom = max(min_denom, self.until - self.start)
        return max(0.0, min(1.0, self.time_left() / denom))

    def child(self, fraction: float) -> "Deadline":
        fraction = max(0.0, min(1.0, fraction))
        dur = (self.until - self.start) * fraction
        return Deadline(seconds=dur)