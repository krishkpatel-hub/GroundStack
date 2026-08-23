from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, select

from app.core.auth import AdminPrincipal
from app.db.session import async_session_factory
from app.models.conversation import TrainingCandidate
from app.schemas.feedback import TrainingCandidateResponse, TrainingCandidateUpdateRequest

router = APIRouter(prefix="/training", tags=["training"])


@router.get("/candidates", response_model=list[TrainingCandidateResponse])
async def list_training_candidates(
    _principal: AdminPrincipal,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TrainingCandidateResponse]:
    async with async_session_factory() as session:
        query = (
            select(TrainingCandidate)
            .where(TrainingCandidate.training_eligible.is_(True))
            .where(TrainingCandidate.source_platform != "discord")
            .order_by(desc(TrainingCandidate.created_at))
        )
        if status_filter:
            query = query.where(TrainingCandidate.status == status_filter)
        rows = await session.execute(query.limit(limit).offset(offset))
        return [
            TrainingCandidateResponse.model_validate(row, from_attributes=True)
            for row in rows.scalars()
        ]


@router.patch("/candidates/{candidate_id}", response_model=TrainingCandidateResponse)
async def update_training_candidate(
    candidate_id: UUID,
    request: TrainingCandidateUpdateRequest,
    _principal: AdminPrincipal,
) -> TrainingCandidateResponse:
    async with async_session_factory() as session:
        candidate = await session.get(TrainingCandidate, candidate_id)
        if candidate is None:
            raise HTTPException(status_code=404, detail="Training candidate not found.")
        for field in [
            "proposed_question",
            "proposed_answer",
            "redaction_status",
            "provenance_status",
            "reviewer_notes",
            "reviewer_identifier",
        ]:
            value = getattr(request, field)
            if value is not None:
                setattr(candidate, field, value)
        if request.status is not None:
            if candidate.source_platform == "discord" or not candidate.training_eligible:
                raise HTTPException(status_code=409, detail="Discord data is not trainable.")
            if request.status == "approved" and (
                candidate.redaction_status != "approved"
                or candidate.provenance_status != "approved"
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Approve redaction and provenance before approving a candidate.",
                )
            candidate.status = request.status
            candidate.reviewed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(candidate)
        return TrainingCandidateResponse.model_validate(candidate, from_attributes=True)
