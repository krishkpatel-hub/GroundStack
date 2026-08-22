from time import perf_counter
from uuid import UUID

import structlog

from app.core.settings import get_settings
from app.db.session import async_session_factory
from app.services.ai.embeddings import SentenceTransformerEmbeddingProvider, get_embedding_provider
from app.services.ai.types import EmbeddingRequest
from app.services.ingestion.checksums import sha256_text
from app.services.ingestion.chunking import ChunkingConfig, StructureAwareChunker
from app.services.ingestion.normalization import normalize_text
from app.services.ingestion.parsers import parser_for
from app.services.ingestion.persistence import KnowledgeRepository
from app.services.ingestion.types import IngestionError, IngestionInput, IngestionReport

logger = structlog.get_logger(__name__)


class IngestionOrchestrator:
    def __init__(
        self, embedding_provider: SentenceTransformerEmbeddingProvider | None = None
    ) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def create_job(self) -> UUID:
        async with async_session_factory() as session:
            repo = KnowledgeRepository(session)
            job = await repo.create_job()
            await session.commit()
            return job.id

    async def ingest(self, job_id: UUID, payload: IngestionInput) -> IngestionReport:
        total_start = perf_counter()
        async with async_session_factory() as session:
            repo = KnowledgeRepository(session)
            job = await repo.get_job(job_id)
            if job is None:
                raise IngestionError("Ingestion job not found.")
            try:
                await repo.update_job(
                    job, status="processing", stage="source_validation", progress=5
                )
                source = await repo.upsert_source(payload)
                job.source_id = source.id
                parser = parser_for(payload.mime_type, payload.display_name)

                extraction_start = perf_counter()
                await repo.update_job(job, stage="content_extraction", progress=20)
                extracted = parser.parse(
                    payload.content, display_name=payload.display_name, mime_type=payload.mime_type
                )
                extraction_duration = perf_counter() - extraction_start

                await repo.update_job(job, stage="normalization", progress=35)
                normalized_text = normalize_text(extracted.text)
                if not normalized_text:
                    raise IngestionError("Document has no usable normalized text.")
                checksum = sha256_text(normalized_text)

                unchanged = await repo.document_by_checksum(source.id, checksum)
                if unchanged is not None:
                    stats = {
                        "document_id": str(unchanged.id),
                        "version": unchanged.version,
                        "chunk_count": len(unchanged.chunks),
                        "skipped_reason": "unchanged_content",
                    }
                    await repo.update_job(
                        job,
                        status="skipped",
                        stage="duplicate_check",
                        progress=100,
                        statistics=stats,
                    )
                    await session.commit()
                    return IngestionReport(
                        job_id=job.id,
                        status="skipped",
                        source_id=source.id,
                        document_id=unchanged.id,
                        version=unchanged.version,
                        chunk_count=len(unchanged.chunks),
                        message="Content unchanged; existing document version reused.",
                    )

                await repo.update_job(job, stage="chunking", progress=50)
                settings = get_settings()
                chunker = StructureAwareChunker(
                    ChunkingConfig(
                        target_tokens=settings.chunk_target_tokens,
                        overlap_tokens=settings.chunk_overlap_tokens,
                    )
                )
                chunks = chunker.chunk(normalized_text)
                if not chunks:
                    raise IngestionError("Document did not produce any chunks.")

                embedding_start = perf_counter()
                await repo.update_job(job, stage="embedding_generation", progress=70)
                embedding_results = await self.embedding_provider.embed(
                    EmbeddingRequest(inputs=[chunk.content for chunk in chunks])
                )
                embedding_duration = perf_counter() - embedding_start

                await repo.update_job(job, stage="transactional_persistence", progress=88)
                document = await repo.create_document_with_chunks(
                    source=source,
                    title=extracted.title,
                    mime_type=payload.mime_type,
                    checksum=checksum,
                    normalized_text=normalized_text,
                    extraction_metadata=extracted.metadata,
                    chunks=chunks,
                    embeddings=[result.vector for result in embedding_results],
                    embedding_model=self.embedding_provider.active_model,
                )
                stats = {
                    "document_id": str(document.id),
                    "version": document.version,
                    "chunk_count": len(chunks),
                    "extraction_duration_seconds": round(extraction_duration, 4),
                    "embedding_duration_seconds": round(embedding_duration, 4),
                    "total_duration_seconds": round(perf_counter() - total_start, 4),
                }
                await repo.update_job(
                    job,
                    status="completed",
                    stage="completed",
                    progress=100,
                    statistics=stats,
                )
                await session.commit()
                logger.info(
                    "ingestion_completed",
                    job_id=str(job.id),
                    source_type=payload.source_type,
                    stage="completed",
                    chunk_count=len(chunks),
                    extraction_duration=extraction_duration,
                    embedding_duration=embedding_duration,
                    total_duration=perf_counter() - total_start,
                )
                return IngestionReport(
                    job_id=job.id,
                    status="completed",
                    source_id=source.id,
                    document_id=document.id,
                    version=document.version,
                    chunk_count=len(chunks),
                    message="Document ingested.",
                )
            except Exception as exc:
                await session.rollback()
                async with async_session_factory() as failure_session:
                    failure_repo = KnowledgeRepository(failure_session)
                    failure_job = await failure_repo.get_job(job_id)
                    if failure_job is not None:
                        category = getattr(exc, "category", "unexpected_error")
                        safe_details = getattr(exc, "safe_details", {})
                        await failure_repo.update_job(
                            failure_job,
                            status="failed",
                            stage="failed",
                            progress=100,
                            statistics={
                                "total_duration_seconds": round(perf_counter() - total_start, 4)
                            },
                            error={
                                "category": category,
                                "message": str(exc),
                                "details": safe_details,
                            },
                        )
                        await failure_session.commit()
                logger.warning(
                    "ingestion_failed",
                    job_id=str(job_id),
                    source_type=payload.source_type,
                    failure_category=getattr(exc, "category", "unexpected_error"),
                )
                raise
