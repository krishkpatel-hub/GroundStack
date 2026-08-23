from __future__ import annotations

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover - redis is optional in local tests
    Redis = None  # type: ignore[assignment]

from app.core.settings import get_settings

_redis_client: Redis | None = None  # type: ignore[valid-type]


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


async def claim_interaction(interaction_id: str) -> bool | None:
    client = await _redis()
    if client is None:
        return None
    settings = get_settings()
    key = f"{settings.redis_key_namespace}:{settings.app_env}:discord:interaction:{interaction_id}"
    try:
        result = await client.set(key, "1", nx=True, ex=settings.discord_queue_ttl_seconds)
    except Exception:
        return None
    return bool(result)
