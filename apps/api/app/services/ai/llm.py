import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.settings import get_settings
from app.services.ai.interfaces import LLMProvider
from app.services.ai.types import (
    GenerationEvent,
    GenerationRequest,
    GenerationResult,
    LLMHealth,
)


class LLMProviderError(RuntimeError):
    def __init__(self, message: str, *, category: str) -> None:
        super().__init__(message)
        self.category = category


class OllamaProvider(LLMProvider):
    provider = "ollama"

    def __init__(self, *, base_url: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = settings.llm_request_timeout_seconds

    async def health(self) -> LLMHealth:
        try:
            available = await self.model_available()
            return LLMHealth(
                provider=self.provider,
                model=self.model,
                reachable=True,
                model_available=available,
                loaded=None,
                detail="ok" if available else "Configured Ollama model is not installed.",
            )
        except LLMProviderError as exc:
            return LLMHealth(
                provider=self.provider,
                model=self.model,
                reachable=False,
                model_available=False,
                loaded=None,
                detail=str(exc),
            )

    async def model_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMProviderError(
                "Ollama is unavailable. Start Ollama and verify LLM_BASE_URL.",
                category="provider_unavailable",
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(str(exc), category="provider_health_failed") from exc
        models = response.json().get("models", [])
        return any(item.get("name") == self.model for item in models)

    def _messages(self, request: GenerationRequest) -> list[dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in request.messages]

    def _payload(self, request: GenerationRequest, *, stream: bool) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": self._messages(request),
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
                "seed": 7,
            },
        }

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if not await self.model_available():
            raise LLMProviderError(
                f"Ollama model '{self.model}' is not installed. Run: ollama pull {self.model}",
                category="model_missing",
            )
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat", json=self._payload(request, stream=False)
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                "Ollama generation timed out.", category="provider_timeout"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(str(exc), category="provider_error") from exc
        payload = response.json()
        return GenerationResult(
            content=payload.get("message", {}).get("content", ""),
            model=payload.get("model", self.model),
            provider=self.provider,
            finish_reason=payload.get("done_reason") or ("stop" if payload.get("done") else None),
            input_tokens=payload.get("prompt_eval_count"),
            output_tokens=payload.get("eval_count"),
        )

    async def stream(self, request: GenerationRequest) -> AsyncIterator[GenerationEvent]:
        if not await self.model_available():
            error_message = (
                f"Ollama model '{self.model}' is not installed. Run: ollama pull {self.model}"
            )
            yield GenerationEvent(
                type="error",
                error_category="model_missing",
                error_message=error_message,
            )
            return
        yield GenerationEvent(type="start")
        content_parts: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/chat", json=self._payload(request, stream=True)
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        payload = json.loads(line)
                        token = payload.get("message", {}).get("content") or ""
                        if token:
                            content_parts.append(token)
                            yield GenerationEvent(type="token", token=token)
                        if payload.get("done"):
                            yield GenerationEvent(
                                type="usage",
                                input_tokens=payload.get("prompt_eval_count"),
                                output_tokens=payload.get("eval_count"),
                            )
                            yield GenerationEvent(
                                type="completed",
                                content="".join(content_parts),
                                finish_reason=payload.get("done_reason") or "stop",
                            )
                            return
        except httpx.TimeoutException:
            yield GenerationEvent(
                type="error", error_category="provider_timeout", error_message="LLM timed out."
            )
        except Exception as exc:
            yield GenerationEvent(
                type="error", error_category="provider_error", error_message=str(exc)
            )


class OpenAICompatibleProvider(LLMProvider):
    provider = "openai_compatible"

    def __init__(self, *, base_url: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.api_key = settings.llm_api_key
        self.timeout = settings.llm_request_timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def health(self) -> LLMHealth:
        try:
            available = await self.model_available()
            return LLMHealth(
                provider=self.provider,
                model=self.model,
                reachable=True,
                model_available=available,
                loaded=None,
                detail="ok" if available else "Configured model not returned by /v1/models.",
            )
        except LLMProviderError as exc:
            return LLMHealth(
                provider=self.provider,
                model=self.model,
                reachable=False,
                model_available=False,
                loaded=None,
                detail=str(exc),
            )

    async def model_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:
                response = await client.get(f"{self.base_url}/v1/models")
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise LLMProviderError(
                "OpenAI-compatible server unavailable.", category="provider_unavailable"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(str(exc), category="provider_health_failed") from exc
        models = response.json().get("data", [])
        return any(item.get("id") == self.model for item in models)

    def _payload(self, request: GenerationRequest, *, stream: bool) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if not await self.model_available():
            raise LLMProviderError(
                f"Model '{self.model}' is unavailable.", category="model_missing"
            )
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=self._payload(request, stream=False),
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderError("Generation timed out.", category="provider_timeout") from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(str(exc), category="provider_error") from exc
        payload = response.json()
        choice = payload.get("choices", [{}])[0]
        usage = payload.get("usage", {})
        return GenerationResult(
            content=choice.get("message", {}).get("content", ""),
            model=payload.get("model", self.model),
            provider=self.provider,
            finish_reason=choice.get("finish_reason"),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )

    async def stream(self, request: GenerationRequest) -> AsyncIterator[GenerationEvent]:
        if not await self.model_available():
            yield GenerationEvent(
                type="error",
                error_category="model_missing",
                error_message=f"Model '{self.model}' is unavailable.",
            )
            return
        yield GenerationEvent(type="start")
        content_parts: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers()) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/chat/completions",
                    json=self._payload(request, stream=True),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line.removeprefix("data: ").strip()
                        if data == "[DONE]":
                            yield GenerationEvent(
                                type="completed",
                                content="".join(content_parts),
                                finish_reason="stop",
                            )
                            return
                        payload = json.loads(data)
                        choice = payload.get("choices", [{}])[0]
                        token = choice.get("delta", {}).get("content") or ""
                        if token:
                            content_parts.append(token)
                            yield GenerationEvent(type="token", token=token)
                        if choice.get("finish_reason"):
                            yield GenerationEvent(
                                type="completed",
                                content="".join(content_parts),
                                finish_reason=choice.get("finish_reason"),
                            )
                            return
        except httpx.TimeoutException:
            yield GenerationEvent(
                type="error", error_category="provider_timeout", error_message="LLM timed out."
            )
        except Exception as exc:
            yield GenerationEvent(
                type="error", error_category="provider_error", error_message=str(exc)
            )


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleProvider()
    return OllamaProvider()
