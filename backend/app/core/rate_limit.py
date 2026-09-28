"""A small in-memory rate limiter for sensitive endpoints such as login.

It counts attempts per key (e.g. an email address) inside a sliding time window.
The counts live in this process's memory, which is right for a single backend
instance. If we ever run several instances, move this into the database or Redis
so the instances share their counts.
"""

import threading
import time
from collections import deque

_PRUNE_THRESHOLD = 10_000


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: float) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def is_limited(self, key: str) -> bool:
        with self._lock:
            return self._count_recent(key) >= self.max_attempts

    def record(self, key: str) -> None:
        with self._lock:
            if len(self._attempts) > _PRUNE_THRESHOLD:
                for stale_key in list(self._attempts):
                    self._count_recent(stale_key)
            self._attempts.setdefault(key, deque()).append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def _count_recent(self, key: str) -> int:
        attempts = self._attempts.get(key)
        if attempts is None:
            return 0
        cutoff = time.monotonic() - self.window_seconds
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if not attempts:
            del self._attempts[key]
        return len(attempts)
