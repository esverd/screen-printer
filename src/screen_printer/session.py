from __future__ import annotations

import time
from collections.abc import Callable


class DevelopSessionTimer:
    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._started_at: float | None = None
        self._ended_at: float | None = None

    @property
    def running(self) -> bool:
        return self._started_at is not None and self._ended_at is None

    def start(self) -> None:
        self._started_at = self._clock()
        self._ended_at = None

    def stop(self) -> float:
        if self._started_at is None:
            return 0.0
        if self._ended_at is None:
            self._ended_at = self._clock()
        return self.elapsed_seconds

    @property
    def elapsed_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        end = self._ended_at if self._ended_at is not None else self._clock()
        return max(0.0, end - self._started_at)


class TripleClickDetector:
    def __init__(self, *, clicks_required: int = 3, window_seconds: float = 0.8) -> None:
        self._clicks_required = max(1, clicks_required)
        self._window_seconds = max(0.05, window_seconds)
        self._click_times: list[float] = []

    def register_click(self, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else float(now)
        first_allowed = current - self._window_seconds
        self._click_times = [click for click in self._click_times if click >= first_allowed]
        self._click_times.append(current)
        if len(self._click_times) >= self._clicks_required:
            self._click_times.clear()
            return True
        return False
