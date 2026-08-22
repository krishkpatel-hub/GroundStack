from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class UrlIngestionRequest(BaseModel):
    url: HttpUrl


class IngestionAcceptedResponse(BaseModel):
    job_id: UUID
    status: str


class IngestionJobResponse(BaseModel):
    id: UUID
    source_id: UUID | None
    status: str
    current_stage: str
    progress: int
    statistics: dict[str, object]
    error: dict[str, object] | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    id: UUID
    source_id: UUID
    source_type: str
    display_name: str
    source_status: str
    version: int
    title: str
    mime_type: str
    content_checksum: str
    chunk_count: int
    ingested_at: datetime


class PaginatedDocumentsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DocumentListItem]


class DocumentDetailResponse(DocumentListItem):
    normalized_text_preview: str
    extraction_metadata: dict[str, object]


class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    position: int
    heading_path: list[str]
    content: str
    token_count: int
    chunk_checksum: str
    embedding_model: str
    chunk_metadata: dict[str, object]
    created_at: datetime


class PaginatedChunksResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DocumentChunkResponse]


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
