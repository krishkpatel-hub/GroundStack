from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.auth import Principal
from app.services.operations import demo_limits


def _request() -> Request:
    return Request({"type": "http", "headers": [], "client": ("203.0.113.10", 1234)})


def _settings(**overrides):
    values = {
        "app_env": "demo",
        "demo_chat_enabled": True,
        "demo_redis_required": False,
        "redis_url": "",
        "demo_daily_question_limit": 100,
        "demo_daily_token_limit": 15000,
        "demo_provider_failure_threshold": 5,
        "demo_provider_failure_window_seconds": 300,
        "demo_allowlist_mode": False,
        "demo_allowlist_ips": [],
        "demo_max_question_length": 40,
        "demo_request_limit_per_minute": 8,
        "llm_max_output_tokens": 500,
        "demo_max_context_tokens": 2500,
        "redis_key_namespace": "test",
        "effective_generation_concurrency": 2,
        "model_queue_timeout_seconds": 0.1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_demo_availability_reports_maintenance(monkeypatch) -> None:
    monkeypatch.setattr(demo_limits, "get_settings", lambda: _settings(demo_chat_enabled=False))

    availability = await demo_limits.demo_availability()

    assert availability.state == "maintenance"
    assert availability.chat_enabled is False


@pytest.mark.asyncio
async def test_demo_chat_rejects_long_question(monkeypatch) -> None:
    monkeypatch.setattr(demo_limits, "get_settings", lambda: _settings())
    principal = Principal(
        subject="anon:test",
        roles=frozenset(["demo_anonymous"]),
        authenticated=False,
        anonymous=True,
        demo=True,
    )

    with pytest.raises(HTTPException) as exc:
        await demo_limits.enforce_demo_chat(_request(), principal, "x" * 80)

    assert exc.value.status_code == 413
