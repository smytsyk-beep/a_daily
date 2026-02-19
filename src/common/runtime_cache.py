# src/common/runtime_cache.py

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int, max_items: int = 10_000) -> None:
        self.ttl_seconds = int(ttl_seconds)
        self.max_items = int(max_items)
        self._store: dict[str, tuple[float, T]] = {}

    def _now(self) -> float:
        return time.time()

    def get(self, key: str) -> T | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at <= self._now():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: T) -> None:
        if len(self._store) >= self.max_items:
            self.prune()
            if len(self._store) >= self.max_items:
                self._store.pop(next(iter(self._store)), None)

        expires_at = self._now() + self.ttl_seconds
        self._store[key] = (expires_at, value)

    def prune(self) -> None:
        now = self._now()
        dead = [k for k, (exp, _) in self._store.items() if exp <= now]
        for k in dead:
            self._store.pop(k, None)

    def delete_by_prefix(self, prefix: str) -> int:
        """Remove all keys starting with prefix. Returns count removed."""
        to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in to_remove:
            self._store.pop(k, None)
        return len(to_remove)


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class RateLimiter:
    """
    Fixed-window limiter.
    Хорош для Telegram MVP: дешево и достаточно.
    """

    def __init__(
        self, max_calls: int, window_seconds: int, max_keys: int = 50_000
    ) -> None:
        self.max_calls = int(max_calls)
        self.window_seconds = int(window_seconds)
        self._buckets: TTLCache[tuple[int, float]] = TTLCache(
            ttl_seconds=window_seconds, max_items=max_keys
        )

    def check(self, key: str) -> RateLimitResult:
        now = time.time()
        bucket = self._buckets.get(key)

        if bucket is None:
            self._buckets.set(key, (1, now))
            return RateLimitResult(True, 0)

        count, window_start = bucket
        window_end = window_start + self.window_seconds

        if now >= window_end:
            self._buckets.set(key, (1, now))
            return RateLimitResult(True, 0)

        if count >= self.max_calls:
            retry = int(window_end - now) + 1
            return RateLimitResult(False, retry)

        self._buckets.set(key, (count + 1, window_start))
        return RateLimitResult(True, 0)
