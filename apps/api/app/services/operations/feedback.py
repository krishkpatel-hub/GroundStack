from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Message, MessageFeedback, TrainingCandidate
from app.schemas.feedback import FeedbackRequest


class FeedbackError(ValueError):
    pass


def message_snapshot(message: Message) -> dict[str, object]:
    return {
        "provider": message.provider,
        "model": message.model,
        "prompt_version": message.prompt_version,
        "retrieval_run_id": str(message.retrieval_run_id) if message.retrieval_run_id else None,
        "generation_run_id": str(message.generation_run_id) if message.generation_run_id else None,
        "grounding_status": message.grounding_status,
    }


class FeedbackRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_feedback(
        self, *, message_id: UUID, request: FeedbackRequest, owner_subject: str | None = None
    ) -> MessageFeedback:
        message = await self.session.get(Message, message_id)
        if message is None or message.role != "assistant":
            raise FeedbackError("Feedback can only be saved for an existing assistant message.")
        if owner_subject and message.owner_subject != owner_subject:
            raise PermissionError("Message belongs to another principal.")
        row = await self.session.execute(
            select(MessageFeedback).where(
                MessageFeedback.message_id == message_id,
                MessageFeedback.client_request_id == request.client_request_id,
            )
        )
        feedback = row.scalar_one_or_none()
        if feedback is None:
            feedback = MessageFeedback(
                message_id=message.id,
                conversation_id=message.conversation_id,
                client_request_id=request.client_request_id,
                owner_subject=owner_subject,
                message_snapshot=message_snapshot(message),
            )
            self.session.add(feedback)
        feedback.rating = request.rating
        feedback.categories = list(request.categories)
        feedback.comment = request.comment
        feedback.suggested_correction = request.suggested_correction
        feedback.citations_incorrect = request.citations_incorrect
        feedback.reported_citation_ids = request.reported_citation_ids
        await self.session.flush()
        return feedback

    async def get_feedback(
        self, *, message_id: UUID, client_request_id: str, owner_subject: str | None = None
    ) -> MessageFeedback | None:
        query = select(MessageFeedback).where(
            MessageFeedback.message_id == message_id,
            MessageFeedback.client_request_id == client_request_id,
        )
        if owner_subject:
            query = query.where(MessageFeedback.owner_subject == owner_subject)
        row = await self.session.execute(query)
        return row.scalar_one_or_none()

    async def delete_feedback(
        self, *, message_id: UUID, client_request_id: str, owner_subject: str | None = None
    ) -> bool:
        feedback = await self.get_feedback(
            message_id=message_id, client_request_id=client_request_id, owner_subject=owner_subject
        )
        if feedback is None:
            return False
        await self.session.delete(feedback)
        await self.session.flush()
        return True

    async def create_candidate(self, *, feedback: MessageFeedback) -> TrainingCandidate:
        message = await self.session.get(Message, feedback.message_id)
        if message is None:
            raise FeedbackError("Message no longer exists.")
        row = await self.session.execute(
            select(TrainingCandidate).where(
                TrainingCandidate.message_id == message.id,
                TrainingCandidate.feedback_id == feedback.id,
            )
        )
        existing = row.scalar_one_or_none()
        if existing:
            return existing
        candidate = TrainingCandidate(
            message_id=message.id,
            feedback_id=feedback.id,
            proposed_question="",
            evidence_snapshot=[],
            proposed_answer=feedback.suggested_correction or message.content,
            citation_references=feedback.reported_citation_ids,
            redaction_status="pending",
            provenance_status="pending",
        )
        self.session.add(candidate)
        await self.session.flush()
        return candidate

    async def approve_candidate(
        self, *, candidate_id: UUID, reviewer_identifier: str, notes: str | None
    ) -> TrainingCandidate:
        candidate = await self.session.get(TrainingCandidate, candidate_id)
        if candidate is None:
            raise FeedbackError("Training candidate not found.")
        if candidate.redaction_status != "approved" or candidate.provenance_status != "approved":
            raise FeedbackError(
                "Candidate requires approved redaction and provenance before approval."
            )
        candidate.status = "approved"
        candidate.reviewer_identifier = reviewer_identifier
        candidate.reviewer_notes = notes
        candidate.reviewed_at = datetime.now(UTC)
        await self.session.flush()
        return candidate
