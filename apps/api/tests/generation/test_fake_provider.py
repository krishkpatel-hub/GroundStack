from types import SimpleNamespace

import pytest

from app.services.ai.llm import FakeLLMProvider
from app.services.ai.types import ChatMessage, GenerationRequest


def _settings(**overrides):
    values = {
        "llm_model": "fake-groundstack",
        "fake_llm_first_token_delay_ms": 0,
        "fake_llm_token_rate_per_second": 1000,
        "fake_llm_total_tokens": 8,
        "fake_llm_failure_mode": "none",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_fake_provider_streams_deterministic_tokens(monkeypatch) -> None:
    monkeypatch.setattr("app.services.ai.llm.get_settings", lambda: _settings())
    provider = FakeLLMProvider()

    events = [
        event
        async for event in provider.stream(
            GenerationRequest(messages=[ChatMessage(role="user", content="question")])
        )
    ]

    assert events[0].type == "start"
    assert any(event.type == "usage" for event in events)
    assert events[-1].type == "completed"


@pytest.mark.asyncio
async def test_fake_provider_can_inject_timeout(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.ai.llm.get_settings", lambda: _settings(fake_llm_failure_mode="timeout")
    )
    provider = FakeLLMProvider()

    events = [
        event
        async for event in provider.stream(
            GenerationRequest(messages=[ChatMessage(role="user", content="question")])
        )
    ]

    assert events[-1].type == "error"
    assert events[-1].error_category == "provider_timeout"
