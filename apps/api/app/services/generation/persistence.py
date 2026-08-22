from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, GenerationRun, Message, MessageCitation
from app.services.ai.types import Citation


def conversation_title(question: str) -> str:
    normalized = " ".join(question.split())
    return normalized[:80] if len(normalized) <= 80 else f"{normalized[:77]}..."


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_conversation(
        self, conversation_id: UUID | None, question: str, owner_subject: str | None = None
    ) -> Conversation:
        if conversation_id is not None:
            conversation = await self.session.get(Conversation, conversation_id)
            if conversation is None:
                raise ValueError("Conversation not found.")
            if owner_subject and conversation.owner_subject not in {None, owner_subject}:
                raise PermissionError("Conversation belongs to another principal.")
            return conversation
        conversation = Conversation(
            title=conversation_title(question), archived=False, owner_subject=owner_subject
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def list_conversations(
        self, *, limit: int, offset: int, owner_subject: str | None = None
    ) -> list[Conversation]:
        query = select(Conversation).where(Conversation.archived.is_(False))
        if owner_subject is not None:
            query = query.where(Conversation.owner_subject == owner_subject)
        rows = await self.session.execute(
            query.order_by(
                Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc()
            )
            .limit(limit)
            .offset(offset)
        )
        return list(rows.scalars().all())

    async def get_conversation(
        self, conversation_id: UUID, owner_subject: str | None = None
    ) -> Conversation | None:
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation and owner_subject and conversation.owner_subject != owner_subject:
            return None
        return conversation

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        rows = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(rows.scalars().all())

    async def create_user_message(
        self, *, conversation: Conversation, content: str, client_request_id: str | None
    ) -> Message:
        if client_request_id:
            existing = await self.session.execute(
                select(Message).where(
                    Message.conversation_id == conversation.id,
                    Message.client_request_id == client_request_id,
                    Message.role == "user",
                )
            )
            found = existing.scalar_one_or_none()
            if found is not None:
                return found
        now = datetime.now(UTC)
        message = Message(
            conversation_id=conversation.id,
            owner_subject=conversation.owner_subject,
            role="user",
            status="completed",
            content=content,
            client_request_id=client_request_id,
            completed_at=now,
        )
        conversation.last_message_at = now
        self.session.add(message)
        await self.session.flush()
        return message

    async def create_assistant_message(
        self,
        *,
        conversation: Conversation,
        content: str,
        status: str,
        grounding_status: str,
        retrieval_run_id: UUID | None,
        generation_run_id: UUID | None,
        provider: str | None,
        model: str | None,
        prompt_version: str | None,
        token_usage: dict[str, int | None] | None = None,
        failure: dict[str, object] | None = None,
    ) -> Message:
        now = datetime.now(UTC)
        message = Message(
            conversation_id=conversation.id,
            owner_subject=conversation.owner_subject,
            role="assistant",
            status=status,
            content=content,
            grounding_status=grounding_status,
            retrieval_run_id=retrieval_run_id,
            generation_run_id=generation_run_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            token_usage=token_usage,
            failure=failure,
            completed_at=now if status == "completed" else None,
        )
        conversation.last_message_at = now
        self.session.add(message)
        await self.session.flush()
        return message

    async def create_generation_run(
        self,
        *,
        conversation_id: UUID,
        retrieval_run_id: UUID | None,
        provider: str,
        model: str,
        prompt_version: str,
        prompt_checksum: str,
        parameters: dict[str, object],
        context_citation_ids: list[str],
        context_token_count: int,
        token_counting_mode: str,
        rendered_prompt: str | None,
    ) -> GenerationRun:
        run = GenerationRun(
            conversation_id=conversation_id,
            retrieval_run_id=retrieval_run_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            prompt_checksum=prompt_checksum,
            generation_parameters=parameters,
            context_citation_ids=context_citation_ids,
            context_token_count=context_token_count,
            token_counting_mode=token_counting_mode,
            rendered_prompt=rendered_prompt,
            status="started",
            started_at=datetime.now(UTC),
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def complete_generation_run(
        self,
        run: GenerationRun,
        *,
        status: str,
        message_id: UUID | None,
        input_tokens: int | None,
        output_tokens: int | None,
        first_token_latency_ms: float | None,
        total_latency_ms: float | None,
        finish_reason: str | None,
        repair_attempt_count: int,
        error: dict[str, object] | None = None,
    ) -> None:
        run.status = status
        run.message_id = message_id
        run.input_tokens = input_tokens
        run.output_tokens = output_tokens
        run.first_token_latency_ms = first_token_latency_ms
        run.total_latency_ms = total_latency_ms
        run.finish_reason = finish_reason
        run.repair_attempt_count = repair_attempt_count
        run.error = error
        run.completed_at = datetime.now(UTC)
        await self.session.flush()

    async def add_message_citations(self, *, message_id: UUID, citations: list[Citation]) -> None:
        for index, citation in enumerate(citations, start=1):
            self.session.add(
                MessageCitation(
                    message_id=message_id,
                    chunk_id=citation.chunk_id,
                    citation_id=citation.citation_id,
                    citation_order=index,
                )
            )
        await self.session.flush()
