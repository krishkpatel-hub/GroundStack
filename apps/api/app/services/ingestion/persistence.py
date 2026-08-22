from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge import Document, DocumentChunk, IngestionJob, KnowledgeSource
from app.services.ingestion.types import DocumentChunkPayload, IngestionInput


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


class KnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_job(self) -> IngestionJob:
        job = IngestionJob(status="queued", current_stage="queued", progress=0, statistics={})
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job(self, job_id: UUID) -> IngestionJob | None:
        return await self.session.get(IngestionJob, job_id)

    async def update_job(
        self,
        job: IngestionJob,
        *,
        status: str | None = None,
        stage: str | None = None,
        progress: int | None = None,
        statistics: dict[str, object] | None = None,
        error: dict[str, object] | None = None,
    ) -> None:
        if status is not None:
            job.status = status
        if stage is not None:
            job.current_stage = stage
        if progress is not None:
            job.progress = progress
        if statistics is not None:
            job.statistics = statistics
        if error is not None:
            job.error = error
        now = datetime.now(UTC)
        if status == "processing" and job.started_at is None:
            job.started_at = now
        if status in {"completed", "failed", "skipped"}:
            job.completed_at = now
        await self.session.flush()

    async def upsert_source(self, payload: IngestionInput) -> KnowledgeSource:
        result = await self.session.execute(
            select(KnowledgeSource).where(
                KnowledgeSource.source_type == payload.source_type,
                KnowledgeSource.canonical_uri == payload.canonical_uri,
            )
        )
        source = result.scalar_one_or_none()
        if source is None:
            source = KnowledgeSource(
                source_type=payload.source_type,
                canonical_uri=payload.canonical_uri,
                display_name=payload.display_name,
                status="active",
                source_metadata=payload.source_metadata,
            )
            self.session.add(source)
        else:
            source.display_name = payload.display_name
            source.source_metadata = payload.source_metadata
        await self.session.flush()
        return source

    async def document_by_checksum(self, source_id: UUID, checksum: str) -> Document | None:
        result = await self.session.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(
                Document.source_id == source_id,
                Document.content_checksum == checksum,
            )
        )
        return result.scalar_one_or_none()

    async def next_version(self, source_id: UUID) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.max(Document.version), 0) + 1).where(
                Document.source_id == source_id
            )
        )
        return int(result.scalar_one())

    async def create_document_with_chunks(
        self,
        *,
        source: KnowledgeSource,
        title: str,
        mime_type: str,
        checksum: str,
        normalized_text: str,
        extraction_metadata: dict[str, object],
        chunks: list[DocumentChunkPayload],
        embeddings: list[list[float]],
        embedding_model: str,
    ) -> Document:
        version = await self.next_version(source.id)
        document = Document(
            source_id=source.id,
            version=version,
            title=title,
            mime_type=mime_type,
            content_checksum=checksum,
            normalized_text=normalized_text,
            extraction_metadata=extraction_metadata,
        )
        self.session.add(document)
        await self.session.flush()
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self.session.add(
                DocumentChunk(
                    document_id=document.id,
                    position=chunk.position,
                    heading_path=chunk.heading_path,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    chunk_checksum=chunk.checksum,
                    embedding=vector_literal(embedding),
                    embedding_model=embedding_model,
                    chunk_metadata=chunk.metadata,
                )
            )
        source.last_successfully_ingested_at = datetime.now(UTC)
        await self.session.flush()
        return document

    async def list_documents(self, *, limit: int, offset: int) -> tuple[int, list[Document]]:
        total = int((await self.session.execute(select(func.count(Document.id)))).scalar_one())
        statement: Select[tuple[Document]] = (
            select(Document)
            .options(selectinload(Document.source), selectinload(Document.chunks))
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.session.execute(statement)).scalars().all()
        return total, list(rows)

    async def get_document(self, document_id: UUID) -> Document | None:
        return await self.session.get(
            Document,
            document_id,
            options=[selectinload(Document.source), selectinload(Document.chunks)],
        )

    async def list_chunks(
        self, document_id: UUID, *, limit: int, offset: int
    ) -> tuple[int, list[DocumentChunk]]:
        total = int(
            (
                await self.session.execute(
                    select(func.count(DocumentChunk.id)).where(
                        DocumentChunk.document_id == document_id
                    )
                )
            ).scalar_one()
        )
        rows = (
            (
                await self.session.execute(
                    select(DocumentChunk)
                    .where(DocumentChunk.document_id == document_id)
                    .order_by(DocumentChunk.position)
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        return total, list(rows)

    async def counts(self) -> dict[str, int]:
        source_count = int(
            (await self.session.execute(select(func.count(KnowledgeSource.id)))).scalar_one()
        )
        document_count = int(
            (await self.session.execute(select(func.count(Document.id)))).scalar_one()
        )
        chunk_count = int(
            (await self.session.execute(select(func.count(DocumentChunk.id)))).scalar_one()
        )
        completed_jobs = int(
            (
                await self.session.execute(
                    select(func.count(IngestionJob.id)).where(IngestionJob.status == "completed")
                )
            ).scalar_one()
        )
        failed_jobs = int(
            (
                await self.session.execute(
                    select(func.count(IngestionJob.id)).where(IngestionJob.status == "failed")
                )
            ).scalar_one()
        )
        return {
            "knowledge_sources": source_count,
            "document_versions": document_count,
            "chunks": chunk_count,
            "completed_ingestion_jobs": completed_jobs,
            "failed_ingestion_jobs": failed_jobs,
        }

    async def index_names(self) -> list[str]:
        rows = await self.session.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename = 'document_chunks'")
        )
        return [str(row[0]) for row in rows]
