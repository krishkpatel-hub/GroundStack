from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.retrieval import CitationResponse, RetrievalFiltersRequest


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)


class ConversationUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    archived: bool | None = None


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    status: str
    content: str
    grounding_status: str | None
    retrieval_run_id: UUID | None
    generation_run_id: UUID | None
    provider: str | None
    model: str | None
    prompt_version: str | None
    token_usage: dict[str, object] | None
    failure: dict[str, object] | None
    citations: list[str] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime | None


class ChatRequest(BaseModel):
    conversation_id: UUID | None = None
    question: str = Field(..., min_length=1)
    client_request_id: str | None = Field(default=None, max_length=120)
    filters: RetrievalFiltersRequest = Field(default_factory=RetrievalFiltersRequest)


class ChatResponse(BaseModel):
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    answer: str
    grounding_status: str
    citations: list[CitationResponse] = Field(default_factory=list)
