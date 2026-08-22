from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID


class IngestionError(Exception):
    category = "ingestion_error"

    def __init__(self, message: str, *, safe_details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.safe_details = safe_details or {}


class UnsupportedSourceError(IngestionError):
    category = "unsupported_source"


class SourceValidationError(IngestionError):
    category = "source_validation"


class ExtractionError(IngestionError):
    category = "extraction"


class EmbeddingError(IngestionError):
    category = "embedding"


@dataclass(frozen=True)
class RawSource:
    source_type: str
    canonical_uri: str
    display_name: str
    mime_type: str
    content: bytes
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractedDocument:
    title: str
    mime_type: str
    text: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class ParsedBlock:
    text: str
    heading_path: tuple[str, ...] = ()
    kind: str = "paragraph"
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentChunkPayload:
    position: int
    heading_path: list[str]
    content: str
    token_count: int
    checksum: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class IngestionInput:
    source_type: str
    canonical_uri: str
    display_name: str
    mime_type: str
    content: bytes
    source_metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IngestionReport:
    job_id: UUID
    status: str
    source_id: UUID | None
    document_id: UUID | None
    version: int | None
    chunk_count: int
    message: str


@dataclass(frozen=True)
class FileSourceRequest:
    path: Path
    display_name: str | None = None
