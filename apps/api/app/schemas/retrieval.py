from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalFiltersRequest(BaseModel):
    source_types: list[str] = Field(default_factory=list)
    source_ids: list[UUID] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)


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
