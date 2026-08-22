from collections.abc import AsyncIterator
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class GenerationRequest(BaseModel):
    messages: list[ChatMessage]
    max_tokens: int = Field(default=512, gt=0)
    temperature: float = Field(default=0.2, ge=0, le=2)
    top_p: float = Field(default=0.9, ge=0, le=1)
    stop: list[str] = Field(default_factory=list)
    stream: bool = False
    request_id: str | None = None


class GenerationResult(BaseModel):
    content: str
    model: str
    provider: str
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMHealth(BaseModel):
    provider: str
    model: str
    reachable: bool
    model_available: bool
    loaded: bool | None = None
    detail: str


class GenerationEvent(BaseModel):
    type: Literal["start", "token", "usage", "completed", "error"]
    token: str | None = None
    content: str | None = None
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_category: str | None = None
    error_message: str | None = None


GenerationStream = AsyncIterator[GenerationEvent]


class EmbeddingRequest(BaseModel):
    inputs: list[str]


class EmbeddingResult(BaseModel):
    text: str
    vector: list[float]


class RetrievalFilters(BaseModel):
    source_types: list[str] = Field(default_factory=list)
    source_ids: list[UUID] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)
    latest_only: bool = True


class RetrievalQuery(BaseModel):
    text: str
    limit: int = Field(default=8, gt=0, le=50)
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    include_debug: bool = False


class RetrievalCandidate(BaseModel):
    source_id: UUID
    document_id: UUID
    document_version: int
    chunk_id: UUID
    chunk_position: int
    title: str
    source_display_name: str
    source_uri: str | None
    source_type: str
    section_path: list[str] = Field(default_factory=list)
    page_number: int | None = None
    chunk_content: str
    chunk_checksum: str
    vector_rank: int | None = None
    vector_distance: float | None = None
    lexical_rank: int | None = None
    lexical_score: float | None = None
    rrf_score: float | None = None
    reranker_score: float | None = None
    final_rank: int | None = None
    selected: bool = False
    exclusion_reason: str | None = None


FusedCandidate = RetrievalCandidate
RerankedCandidate = RetrievalCandidate


class Citation(BaseModel):
    citation_id: str
    source_id: UUID
    document_id: UUID
    document_version: int
    chunk_id: UUID
    title: str
    source_display_name: str
    source_type: str
    source_uri: str | None
    section_path: str | None
    page_number: int | None
    excerpt: str
    final_rank: int


class RetrievalTrace(BaseModel):
    query_hash: str
    query_length: int
    vector_candidate_count: int = 0
    lexical_candidate_count: int = 0
    fused_candidate_count: int = 0
    reranked_candidate_count: int = 0
    final_result_count: int = 0
    reranking_applied: bool = False
    reranking_mode: Literal["enabled", "disabled", "degraded"] = "disabled"
    degraded_mode: dict[str, str] | None = None
    latency_ms: dict[str, float] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    retrieval_run_id: UUID | None = None
    normalized_query: str
    result_count: int
    evidence_found: bool
    reranking_applied: bool
    degraded_mode: dict[str, str] | None = None
    applied_filters: RetrievalFilters
    citations: list[Citation]
    candidates: list[RetrievalCandidate] = Field(default_factory=list)
    trace: RetrievalTrace
