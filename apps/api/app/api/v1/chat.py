import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.auth import ChatPrincipal, Principal
from app.core.settings import get_settings
from app.schemas.conversation import ChatRequest, ChatResponse
from app.services.ai.types import RetrievalFilters
from app.services.generation.service import GroundedAnswerService
from app.services.operations.demo_limits import (
    distributed_generation_slot,
    enforce_demo_chat,
    record_provider_failure,
)
from app.services.operations.metrics import metrics
from app.services.operations.rate_limit import BackpressureError, gate, limiter

router = APIRouter(prefix="/chat", tags=["chat"])


def _filters(request: ChatRequest) -> RetrievalFilters:
    return RetrievalFilters(
        source_types=request.filters.source_types,
        source_ids=request.filters.source_ids,
        document_ids=request.filters.document_ids,
    )


def _client_key(request: Request, principal: Principal | None = None) -> str:
    if principal is not None:
        return f"chat:{principal.subject}"
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    host = forwarded or (request.client.host if request.client else "local")
    return f"chat:{host}"


async def _enforce_chat_limit(request: Request, principal: Principal | None = None) -> None:
    settings = get_settings()
    limit = (
        settings.demo_request_limit_per_minute
        if principal and principal.demo
        else settings.chat_rate_limit_per_minute
    )
    decision = await limiter("chat", limit=limit).check(_client_key(request, principal))
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many chat requests.",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    principal: ChatPrincipal,
) -> ChatResponse:
    await enforce_demo_chat(http_request, principal, request.question)
    await _enforce_chat_limit(http_request, principal)
    settings = get_settings()
    try:
        async with (
            distributed_generation_slot(),
            gate(
                "generation",
                max_concurrency=settings.effective_generation_concurrency,
                timeout_seconds=settings.model_queue_timeout_seconds,
            ).acquire(),
        ):
            result = await GroundedAnswerService().answer(
                question=request.question,
                conversation_id=request.conversation_id,
                client_request_id=request.client_request_id,
                filters=_filters(request),
                owner_subject=principal.subject,
            )
    except BackpressureError as exc:
        metrics.increment("groundstack_backpressure_total", operation="chat", result="busy")
        raise HTTPException(status_code=503, detail=str(exc), headers={"Retry-After": "3"}) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return ChatResponse(
        conversation_id=result.get("conversation_id"),
        message_id=result.get("message_id"),
        answer=str(result.get("answer", "")),
        grounding_status=str(result.get("grounding_status", "generation_failed")),
        citations=result.get("citations", []),
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    http_request: Request,
    principal: ChatPrincipal,
) -> StreamingResponse:
    await enforce_demo_chat(http_request, principal, request.question)
    await _enforce_chat_limit(http_request, principal)
    settings = get_settings()
    service = GroundedAnswerService()

    async def events():
        try:
            async with (
                distributed_generation_slot(),
                gate(
                    "generation",
                    max_concurrency=settings.effective_generation_concurrency,
                    timeout_seconds=settings.model_queue_timeout_seconds,
                ).acquire(),
            ):
                async for event in service.stream_answer(
                    question=request.question,
                    conversation_id=request.conversation_id,
                    client_request_id=request.client_request_id,
                    filters=_filters(request),
                    owner_subject=principal.subject,
                ):
                    if event.event == "error":
                        await record_provider_failure(str(event.data.get("category", "")))
                    yield f"event: {event.event}\n"
                    yield f"data: {json.dumps(event.data)}\n\n"
        except BackpressureError as exc:
            metrics.increment("groundstack_backpressure_total", operation="chat", result="busy")
            yield "event: error\n"
            yield f"data: {json.dumps({'message': str(exc), 'category': 'backpressure'})}\n\n"
        except PermissionError as exc:
            yield "event: error\n"
            yield f"data: {json.dumps({'message': str(exc), 'category': 'authorization'})}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
