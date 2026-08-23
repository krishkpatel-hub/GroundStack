from types import SimpleNamespace

import pytest

from app.services.discord import replay


class FakeRedis:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    async def set(self, key: str, value: str, *, nx: bool, ex: int) -> bool:
        assert value == "1"
        assert nx is True
        assert ex == 900
        if key in self.keys:
            return False
        self.keys.add(key)
        return True


@pytest.mark.asyncio
async def test_claim_interaction_uses_redis_set_nx(monkeypatch) -> None:
    fake = FakeRedis()

    async def fake_redis() -> FakeRedis:
        return fake

    monkeypatch.setattr(replay, "_redis", fake_redis)
    monkeypatch.setattr(
        replay,
        "get_settings",
        lambda: SimpleNamespace(
            redis_key_namespace="groundstack",
            app_env="test",
            discord_queue_ttl_seconds=900,
        ),
    )

    assert await replay.claim_interaction("abc") is True
    assert await replay.claim_interaction("abc") is False


@pytest.mark.asyncio
async def test_claim_interaction_returns_none_without_redis(monkeypatch) -> None:
    async def no_redis() -> None:
        return None

    monkeypatch.setattr(replay, "_redis", no_redis)

    assert await replay.claim_interaction("abc") is None
