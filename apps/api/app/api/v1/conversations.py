from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import select

from app.core.auth import ChatPrincipal
from app.db.session import async_session_factory
from app.models.conversation import Conversation, MessageCitation, MessageFeedback
from app.models.knowledge import Document, DocumentChunk, KnowledgeSource
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    ConversationUpdateRequest,
    MessageFeedbackSummary,
    MessageResponse,
)
from app.schemas.retrieval import CitationResponse
from app.services.generation.persistence import ConversationRepository
from app.services.retrieval.repository import metadata_page_number
from app.services.retrieval.selection import excerpt_text

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _conversation_response(conversation: Conversation) -> ConversationResponse:
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        archived=conversation.archived,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_message_at=conversation.last_message_at,
    )


def _message_response(
    message, *, citations: list[CitationResponse], feedback: MessageFeedback | None
) -> MessageResponse:
    return MessageResponse.model_validate(message, from_attributes=True).model_copy(
        update={
            "citations": citations,
            "feedback": (
                MessageFeedbackSummary.model_validate(feedback, from_attributes=True)
                if feedback
                else None
            ),
        }
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    principal: ChatPrincipal,
) -> ConversationResponse:
    async with async_session_factory() as session:
        conversation = Conversation(
            title=request.title or "New conversation",
            archived=False,
            owner_subject=principal.subject,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return _conversation_response(conversation)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    principal: ChatPrincipal,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ConversationResponse]:
    async with async_session_factory() as session:
        conversations = await ConversationRepository(session).list_conversations(
            limit=limit, offset=offset, owner_subject=principal.subject
        )
        return [_conversation_response(conversation) for conversation in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    principal: ChatPrincipal,
) -> ConversationResponse:
    async with async_session_factory() as session:
        conversation = await ConversationRepository(session).get_conversation(
            conversation_id, owner_subject=principal.subject
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return _conversation_response(conversation)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: ConversationUpdateRequest,
    principal: ChatPrincipal,
) -> ConversationResponse:
    async with async_session_factory() as session:
        conversation = await ConversationRepository(session).get_conversation(
            conversation_id, owner_subject=principal.subject
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        if request.title is not None:
            conversation.title = request.title
        if request.archived is not None:
            conversation.archived = request.archived
        await session.commit()
        await session.refresh(conversation)
        return _conversation_response(conversation)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    principal: ChatPrincipal,
) -> Response:
    async with async_session_factory() as session:
        conversation = await ConversationRepository(session).get_conversation(
            conversation_id, owner_subject=principal.subject
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        conversation.archived = True
        await session.commit()
    return Response(status_code=204)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    principal: ChatPrincipal,
    conversation_id: UUID,
) -> list[MessageResponse]:
    async with async_session_factory() as session:
        repo = ConversationRepository(session)
        if await repo.get_conversation(conversation_id, owner_subject=principal.subject) is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        messages = await repo.list_messages(conversation_id)
        message_ids = [message.id for message in messages]
        citations_by_message: dict[UUID, list[CitationResponse]] = {
            message_id: [] for message_id in message_ids
        }
        feedback_by_message = {}
        if message_ids:
            rows = await session.execute(
                select(MessageCitation, DocumentChunk, Document, KnowledgeSource)
                .join(DocumentChunk, DocumentChunk.id == MessageCitation.chunk_id)
                .join(Document, Document.id == DocumentChunk.document_id)
                .join(KnowledgeSource, KnowledgeSource.id == Document.source_id)
                .where(MessageCitation.message_id.in_(message_ids))
                .order_by(MessageCitation.message_id, MessageCitation.citation_order)
            )
            for citation, chunk, document, source in rows:
                citations_by_message[citation.message_id].append(
                    CitationResponse(
                        citation_id=citation.citation_id,
                        source_id=source.id,
                        document_id=document.id,
                        document_version=document.version,
                        chunk_id=chunk.id,
                        title=document.title,
                        source_display_name=source.display_name,
                        source_type=source.source_type,
                        source_uri=source.canonical_uri,
                        section_path=(
                            " > ".join(chunk.heading_path) if chunk.heading_path else None
                        ),
                        page_number=metadata_page_number(dict(chunk.chunk_metadata or {})),
                        excerpt=excerpt_text(chunk.content),
                        final_rank=citation.citation_order,
                    )
                )
            feedback_rows = await session.execute(
                select(MessageFeedback)
                .where(
                    MessageFeedback.message_id.in_(message_ids),
                    MessageFeedback.owner_subject == principal.subject,
                )
                .order_by(MessageFeedback.updated_at.desc())
            )
            for feedback in feedback_rows.scalars():
                feedback_by_message.setdefault(feedback.message_id, feedback)
        return [
            _message_response(
                message,
                citations=citations_by_message[message.id],
                feedback=feedback_by_message.get(message.id),
            )
            for message in messages
        ]
