from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class TokenBucketLimiter:
    def __init__(self, *, limit: int, window_seconds: int = 60) -> None:
        self.limit = max(1, limit)
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> RateLimitDecision:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        async with self._lock:
            entries = [item for item in self._buckets.get(key, []) if item > cutoff]
            if len(entries) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - entries[0])))
                self._buckets[key] = entries
                return RateLimitDecision(False, retry_after)
            entries.append(now)
            self._buckets[key] = entries
            return RateLimitDecision(True, 0)


class BackpressureGate:
    def __init__(self, *, max_concurrency: int, timeout_seconds: float) -> None:
        self.max_concurrency = max(1, max_concurrency)
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self.timeout_seconds = max(0.05, timeout_seconds)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.timeout_seconds)
        except TimeoutError as exc:
            raise BackpressureError(
                f"Service is at capacity. Retry after {int(self.timeout_seconds) or 1} seconds."
            ) from exc
        try:
            yield
        finally:
            self._semaphore.release()


class BackpressureError(RuntimeError):
    pass


_limiters: dict[str, TokenBucketLimiter] = {}
_gates: dict[str, BackpressureGate] = {}


def limiter(name: str, *, limit: int) -> TokenBucketLimiter:
    current = _limiters.get(name)
    if current is None or current.limit != max(1, limit):
        current = TokenBucketLimiter(limit=limit)
        _limiters[name] = current
    return current


def gate(name: str, *, max_concurrency: int, timeout_seconds: float) -> BackpressureGate:
    current = _gates.get(name)
    if (
        current is None
        or current.timeout_seconds != max(0.05, timeout_seconds)
        or current.max_concurrency != max(1, max_concurrency)
    ):
        current = BackpressureGate(max_concurrency=max_concurrency, timeout_seconds=timeout_seconds)
        _gates[name] = current
    return current
