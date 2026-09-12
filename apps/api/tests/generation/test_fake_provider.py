from types import SimpleNamespace

import pytest

from app.services.ai.llm import (
    FakeLLMProvider,
    LLMProviderError,
    OllamaProvider,
    OpenAICompatibleProvider,
)
from app.services.ai.types import ChatMessage, GenerationRequest


def _settings(**overrides):
    values = {
        "llm_model": "fake-groundstack",
        "llm_base_url": "http://provider.invalid",
        "llm_api_key": "",
        "effective_llm_timeout_seconds": 1,
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


@pytest.mark.parametrize("provider_class", [OllamaProvider, OpenAICompatibleProvider])
@pytest.mark.asyncio
async def test_real_provider_stream_reports_unavailable_model_as_event(
    monkeypatch, provider_class
) -> None:
    monkeypatch.setattr("app.services.ai.llm.get_settings", lambda: _settings())
    provider = provider_class()

    async def unavailable() -> bool:
        raise LLMProviderError(
            "private provider connection detail",
            category="provider_unavailable",
        )

    monkeypatch.setattr(provider, "model_available", unavailable)
    events = [
        event
        async for event in provider.stream(
            GenerationRequest(messages=[ChatMessage(role="user", content="question")])
        )
    ]

    assert len(events) == 1
    assert events[0].type == "error"
    assert events[0].error_category == "provider_unavailable"
    assert events[0].error_message == "The language model provider is unavailable."
