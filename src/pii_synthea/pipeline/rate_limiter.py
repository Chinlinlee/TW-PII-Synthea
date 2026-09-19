"""
Rate Limiter for throttling batch generation and API calls.
"""

from __future__ import annotations

import time
from typing import Optional


class RateLimiter:
    """
    Simple interval-based rate limiter to control calls per second.
    If rate_limit_per_sec is None or <= 0, no throttling is applied.
    """

    def __init__(self, rate_limit_per_sec: Optional[float] = None) -> None:
        self.rate_limit_per_sec = rate_limit_per_sec
        self.interval = (1.0 / rate_limit_per_sec) if rate_limit_per_sec and rate_limit_per_sec > 0 else 0.0
        self.last_call: float = 0.0

    def acquire(self) -> None:
        """Throttles execution if calling faster than configured rate limit."""
        if self.interval <= 0:
            return

        now = time.perf_counter()
        elapsed = now - self.last_call
        wait_time = self.interval - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
            self.last_call = time.perf_counter()
        else:
            self.last_call = now
