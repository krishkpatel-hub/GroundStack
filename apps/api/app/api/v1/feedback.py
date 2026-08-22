from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.core.auth import ChatPrincipal
from app.core.settings import get_settings
from app.db.session import async_session_factory
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.operations.feedback import FeedbackError, FeedbackRepository
from app.services.operations.metrics import metrics
from app.services.operations.rate_limit import limiter

router = APIRouter(prefix="/messages", tags=["feedback"])


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    host = forwarded or (request.client.host if request.client else "local")
    return f"feedback:{host}"


def _feedback_response(feedback) -> FeedbackResponse:
    return FeedbackResponse.model_validate(feedback, from_attributes=True)


async def _enforce_feedback_limit(request: Request) -> None:
    settings = get_settings()
    decision = await limiter("feedback", limit=settings.feedback_rate_limit_per_minute).check(
        _client_key(request)
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many feedback requests.",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


@router.put("/{message_id}/feedback", response_model=FeedbackResponse)
async def put_feedback(
    message_id: UUID,
    payload: FeedbackRequest,
    request: Request,
    principal: ChatPrincipal,
) -> FeedbackResponse:
    await _enforce_feedback_limit(request)
    async with async_session_factory() as session:
        repo = FeedbackRepository(session)
        try:
            feedback = await repo.upsert_feedback(
                message_id=message_id, request=payload, owner_subject=principal.subject
            )
        except FeedbackError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        await session.commit()
        await session.refresh(feedback)
        metrics.increment("groundstack_feedback_total", operation=payload.rating, result="saved")
        return _feedback_response(feedback)


@router.get("/{message_id}/feedback", response_model=FeedbackResponse)
async def get_feedback(
    message_id: UUID,
    client_request_id: Annotated[str, Query(min_length=1, max_length=120)],
    request: Request,
    principal: ChatPrincipal,
) -> FeedbackResponse:
    await _enforce_feedback_limit(request)
    async with async_session_factory() as session:
        feedback = await FeedbackRepository(session).get_feedback(
            message_id=message_id,
            client_request_id=client_request_id,
            owner_subject=principal.subject,
        )
        if feedback is None:
            raise HTTPException(status_code=404, detail="Feedback not found.")
        return _feedback_response(feedback)


@router.delete("/{message_id}/feedback", status_code=204)
async def delete_feedback(
    message_id: UUID,
    client_request_id: Annotated[str, Query(min_length=1, max_length=120)],
    request: Request,
    principal: ChatPrincipal,
) -> Response:
    await _enforce_feedback_limit(request)
    async with async_session_factory() as session:
        deleted = await FeedbackRepository(session).delete_feedback(
            message_id=message_id,
            client_request_id=client_request_id,
            owner_subject=principal.subject,
        )
        await session.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    metrics.increment("groundstack_feedback_total", operation="delete", result="deleted")
    return Response(status_code=204)
