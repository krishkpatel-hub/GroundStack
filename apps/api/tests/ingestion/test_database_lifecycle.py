import asyncio
import os
import sys
from uuid import uuid4

import asyncpg
import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.knowledge import Document, DocumentChunk, IngestionJob, KnowledgeSource
from app.services.ai.types import EmbeddingResult
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.ingestion.persistence import KnowledgeRepository
from app.services.ingestion.types import EmbeddingError, IngestionInput


@pytest.mark.integration
async def test_ingestion_rollback_retry_deduplication_and_delete(monkeypatch):
    configured = os.getenv("DATABASE_URL")
    if not configured:
        pytest.skip("DATABASE_URL is required to create an isolated test database.")
    source = make_url(configured)
    database = f"groundstack_test_{uuid4().hex}"
    maintenance = source.set(drivername="postgresql", database="postgres")
    connection = await asyncpg.connect(maintenance.render_as_string(hide_password=False))
    engine = None
    try:
        await connection.execute(f'CREATE DATABASE "{database}"')
        url = source.set(database=database).render_as_string(hide_password=False)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
            env={**os.environ, "DATABASE_URL": url, "DATABASE_DIRECT_URL": ""},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        assert process.returncode == 0, "Isolated database migrations failed."
        engine = create_async_engine(url)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        monkeypatch.setattr("app.services.ingestion.orchestrator.async_session_factory", sessions)

        class TestEmbeddings:
            active_model = "isolated-test-embeddings"
            fail = True

            async def embed(self, request):
                if self.fail:
                    raise EmbeddingError("Embedding provider unavailable.")
                return [
                    EmbeddingResult(text=text, vector=[1.0] + [0.0] * 383)
                    for text in request.inputs
                ]

        embeddings = TestEmbeddings()
        orchestrator = IngestionOrchestrator(embedding_provider=embeddings)
        payload = IngestionInput(
            source_type="file",
            canonical_uri="file://isolated-reference.md",
            display_name="isolated-reference.md",
            mime_type="text/markdown",
            content=b"# Configuration\n\nRefresh the configuration and restart the worker.",
        )
        job_id = await orchestrator.create_job()
        with pytest.raises(EmbeddingError):
            await orchestrator.ingest(job_id, payload)
        async with sessions() as session:
            job = await session.get(IngestionJob, job_id)
            assert job.status == "failed"
            assert job.error["category"] == "embedding"
            assert await session.scalar(select(func.count()).select_from(Document)) == 0
            assert await session.scalar(select(func.count()).select_from(DocumentChunk)) == 0

        embeddings.fail = False
        completed = await orchestrator.ingest(await orchestrator.create_job(), payload)
        duplicate = await orchestrator.ingest(await orchestrator.create_job(), payload)
        assert completed.status == "completed"
        assert duplicate.status == "skipped"
        assert duplicate.document_id == completed.document_id
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(Document)) == 1
            assert (
                await session.scalar(select(func.count()).select_from(DocumentChunk))
                == completed.chunk_count
            )
            repo = KnowledgeRepository(session)
            document = await repo.get_document(completed.document_id)
            assert "restart the worker" in document.chunks[0].content
            await repo.delete_document(document)
            await session.commit()
        async with sessions() as session:
            assert await session.scalar(select(func.count()).select_from(Document)) == 0
            assert await session.scalar(select(func.count()).select_from(DocumentChunk)) == 0
            assert (await session.get(KnowledgeSource, completed.source_id)).status == "deleted"
    finally:
        if engine is not None:
            await engine.dispose()
        await connection.execute(f'DROP DATABASE IF EXISTS "{database}" WITH (FORCE)')
        await connection.close()
