from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalFiltersRequest(BaseModel):
    source_types: list[str] = Field(default_factory=list)
    source_ids: list[UUID] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)


class RetrievalSearchRequest(BaseModel):
    query: str = Field(..., description="Technical question or search phrase.")
    top_k: int = Field(default=8, ge=1, le=20)
    filters: RetrievalFiltersRequest = Field(default_factory=RetrievalFiltersRequest)
    include_debug: bool = False


class CitationResponse(BaseModel):
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


class RetrievalTraceResponse(BaseModel):
    query_hash: str
    query_length: int
    vector_candidate_count: int
    lexical_candidate_count: int
    fused_candidate_count: int
    reranked_candidate_count: int
    final_result_count: int
    reranking_applied: bool
    reranking_mode: str
    degraded_mode: dict[str, str] | None
    latency_ms: dict[str, float]


class RetrievalCandidateDebugResponse(BaseModel):
    source_id: UUID
    document_id: UUID
    document_version: int
    chunk_id: UUID
    chunk_position: int
    title: str
    source_display_name: str
    source_uri: str | None
    source_type: str
    section_path: list[str]
    page_number: int | None
    chunk_content: str
    vector_rank: int | None
    vector_distance: float | None
    lexical_rank: int | None
    lexical_score: float | None
    rrf_score: float | None
    reranker_score: float | None
    final_rank: int | None
    selected: bool
    exclusion_reason: str | None


class RetrievalSearchResponse(BaseModel):
    retrieval_run_id: UUID | None
    normalized_query: str
    result_count: int
    evidence_found: bool
    reranking_applied: bool
    degraded_mode: dict[str, str] | None
    applied_filters: RetrievalFiltersRequest
    citations: list[CitationResponse]
    timings_ms: dict[str, float]
    debug: list[RetrievalCandidateDebugResponse] | None = None


class RetrievalConfigResponse(BaseModel):
    algorithm_version: str
    vector_candidate_limit: int
    lexical_candidate_limit: int
    rrf_k: int
    vector_rrf_weight: float
    lexical_rrf_weight: float
    rerank_candidate_limit: int
    final_top_k: int
    max_top_k: int
    max_chunks_per_source: int
    reranking_enabled: bool
    reranker_provider: str
    reranker_model: str
    persist_retrieval_queries: bool
    debug_enabled: bool


class RetrievalRunResultResponse(BaseModel):
    chunk_id: UUID
    vector_rank: int | None
    vector_distance: float | None
    lexical_rank: int | None
    lexical_score: float | None
    rrf_score: float | None
    reranker_score: float | None
    final_rank: int | None
    selected: bool
    exclusion_reason: str | None


class RetrievalRunDetailResponse(BaseModel):
    id: UUID
    query_text: str | None
    query_hash: str
    query_length: int
    applied_filters: dict[str, object]
    configuration: dict[str, object]
    algorithm_version: str
    candidate_counts: dict[str, object]
    reranking_mode: str
    degraded_mode: dict[str, object] | None
    latency_ms: dict[str, object]
    created_at: datetime
    total: int
    limit: int
    offset: int
    results: list[RetrievalRunResultResponse]
