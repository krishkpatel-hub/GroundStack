from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256

from fastapi import HTTPException, Request

from app.core.auth import Principal
from app.core.settings import get_settings
from app.services.operations.metrics import metrics

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover - dependency presence is verified in deployment checks.
    Redis = None  # type: ignore[assignment]


@dataclass(frozen=True)
class DemoAvailability:
    state: str
    chat_enabled: bool
    reason: str
    retry_after_seconds: int | None = None


class _LocalCounters:
    def __init__(self) -> None:
        self._values: dict[str, tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    async def incr(self, key: str, *, ttl_seconds: int) -> int:
        now = time.time()
        async with self._lock:
            value, expires_at = self._values.get(key, (0, now + ttl_seconds))
            if expires_at <= now:
                value, expires_at = 0, now + ttl_seconds
            value += 1
            self._values[key] = (value, expires_at)
            return value

    async def get(self, key: str) -> int:
        now = time.time()
        async with self._lock:
            value, expires_at = self._values.get(key, (0, 0))
            return value if expires_at > now else 0

    async def ping(self) -> bool:
        return True


_local_counters = _LocalCounters()
_redis_client: Redis | None = None  # type: ignore[valid-type]
_generation_lock = asyncio.Semaphore(1)
_generation_lock_size = 1


def _settings_prefix() -> str:
    settings = get_settings()
    return f"{settings.redis_key_namespace}:{settings.app_env}:demo"


def _today_key() -> str:
    return datetime.now(UTC).strftime("%Y%m%d")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "unknown")


def _client_hash(request: Request) -> str:
    return sha256(_client_ip(request).encode("utf-8")).hexdigest()[:24]


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


async def _redis() -> Redis | None:  # type: ignore[valid-type]
    global _redis_client
    settings = get_settings()
    if not settings.redis_url or Redis is None:
        return None
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=settings.redis_timeout_seconds,
            socket_timeout=settings.redis_timeout_seconds,
            decode_responses=True,
        )
    return _redis_client


async def _counter_incr(key: str, *, ttl_seconds: int, amount: int = 1) -> int:
    client = await _redis()
    if client is None:
        value = 0
        for _ in range(max(1, amount)):
            value = await _local_counters.incr(key, ttl_seconds=ttl_seconds)
        return value
    value = await client.incrby(key, amount)
    if value == amount:
        await client.expire(key, ttl_seconds)
    return int(value)


async def _counter_get(key: str) -> int:
    client = await _redis()
    if client is None:
        return await _local_counters.get(key)
    value = await client.get(key)
    return int(value or 0)


async def _counter_decr(key: str) -> None:
    client = await _redis()
    if client is not None:
        await client.decr(key)


async def redis_connectivity_ok() -> bool:
    client = await _redis()
    if client is None:
        return not get_settings().demo_redis_required
    try:
        return bool(await client.ping())
    except Exception:
        return False


async def demo_availability() -> DemoAvailability:
    settings = get_settings()
    if settings.app_env != "demo":
        return DemoAvailability(state="available", chat_enabled=True, reason="not_demo")
    if not settings.demo_chat_enabled:
        return DemoAvailability(
            state="maintenance", chat_enabled=False, reason="demo_chat_disabled"
        )
    if settings.demo_redis_required and not await redis_connectivity_ok():
        return DemoAvailability(
            state="temporarily_limited", chat_enabled=False, reason="capacity_store_unavailable"
        )
    prefix = _settings_prefix()
    daily_questions = await _counter_get(f"{prefix}:questions:{_today_key()}")
    if daily_questions >= settings.demo_daily_question_limit:
        return DemoAvailability(
            state="daily_capacity_reached",
            chat_enabled=False,
            reason="daily_question_limit_reached",
        )
    daily_tokens = await _counter_get(f"{prefix}:tokens:{_today_key()}")
    if daily_tokens >= settings.demo_daily_token_limit:
        return DemoAvailability(
            state="daily_capacity_reached",
            chat_enabled=False,
            reason="daily_token_limit_reached",
        )
    failures = await _counter_get(f"{prefix}:provider_failures")
    if failures >= settings.demo_provider_failure_threshold:
        return DemoAvailability(
            state="inference_unavailable",
            chat_enabled=False,
            reason="provider_circuit_open",
            retry_after_seconds=settings.demo_provider_failure_window_seconds,
        )
    return DemoAvailability(state="available", chat_enabled=True, reason="ok")


async def enforce_demo_chat(request: Request, principal: Principal, question: str) -> None:
    settings = get_settings()
    if not principal.demo:
        return
    availability = await demo_availability()
    if not availability.chat_enabled:
        raise HTTPException(
            status_code=503,
            detail="The public demo is temporarily unavailable.",
            headers={"Retry-After": str(availability.retry_after_seconds or 60)},
        )
    if settings.demo_allowlist_mode and _client_ip(request) not in settings.demo_allowlist_ips:
        raise HTTPException(status_code=403, detail="This demo is currently allowlisted.")
    if len(question) > settings.demo_max_question_length:
        raise HTTPException(status_code=413, detail="Question is too long for the public demo.")

    prefix = _settings_prefix()
    client = _client_hash(request)
    minute = int(time.time() // 60)
    per_client = await _counter_incr(f"{prefix}:client:{client}:minute:{minute}", ttl_seconds=90)
    if per_client > settings.demo_request_limit_per_minute:
        metrics.increment("groundstack_demo_rate_limit_total", scope="client")
        raise HTTPException(
            status_code=429,
            detail="The public demo rate limit was reached. Please try again shortly.",
            headers={"Retry-After": "60"},
        )

    day = _today_key()
    questions = await _counter_incr(f"{prefix}:questions:{day}", ttl_seconds=90000)
    if questions > settings.demo_daily_question_limit:
        metrics.increment("groundstack_demo_rate_limit_total", scope="daily_questions")
        raise HTTPException(
            status_code=429,
            detail="The public demo reached today's question capacity.",
            headers={"Retry-After": "3600"},
        )

    token_budget = _estimate_tokens(question) + settings.llm_max_output_tokens
    if token_budget + settings.demo_max_context_tokens > settings.demo_daily_token_limit:
        raise HTTPException(status_code=413, detail="Question exceeds the public demo budget.")
    tokens = await _counter_incr(f"{prefix}:tokens:{day}", ttl_seconds=90000, amount=token_budget)
    if tokens > settings.demo_daily_token_limit:
        metrics.increment("groundstack_demo_rate_limit_total", scope="daily_tokens")
        raise HTTPException(
            status_code=429,
            detail="The public demo reached today's generation capacity.",
            headers={"Retry-After": "3600"},
        )


async def record_provider_failure(category: str | None) -> None:
    settings = get_settings()
    if settings.app_env != "demo" or category in {None, "model_missing"}:
        return
    await _counter_incr(
        f"{_settings_prefix()}:provider_failures",
        ttl_seconds=settings.demo_provider_failure_window_seconds,
    )


@asynccontextmanager
async def distributed_generation_slot() -> AsyncIterator[None]:
    settings = get_settings()
    client = await _redis()
    if client is not None:
        key = f"{_settings_prefix()}:generation_active"
        active = await client.incr(key)
        await client.expire(key, max(30, int(settings.effective_llm_timeout_seconds) + 10))
        if active > settings.effective_generation_concurrency:
            await client.decr(key)
            raise HTTPException(
                status_code=503,
                detail="The public demo is busy. Please retry shortly.",
                headers={"Retry-After": "3"},
            )
        try:
            yield
        finally:
            await _counter_decr(key)
        return

    global _generation_lock, _generation_lock_size
    if _generation_lock_size != settings.effective_generation_concurrency:
        _generation_lock = asyncio.Semaphore(settings.effective_generation_concurrency)
        _generation_lock_size = settings.effective_generation_concurrency
    try:
        await asyncio.wait_for(
            _generation_lock.acquire(), timeout=settings.model_queue_timeout_seconds
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="The public demo is busy. Please retry shortly.",
            headers={"Retry-After": "3"},
        ) from exc
    try:
        yield
    finally:
        _generation_lock.release()
