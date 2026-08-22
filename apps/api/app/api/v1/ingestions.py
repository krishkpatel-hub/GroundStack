from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from app.core.auth import AdminPrincipal
from app.core.settings import get_settings
from app.db.session import async_session_factory
from app.models.knowledge import IngestionJob
from app.schemas.ingestion import (
    IngestionAcceptedResponse,
    IngestionJobResponse,
    UrlIngestionRequest,
)
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.ingestion.persistence import KnowledgeRepository
from app.services.ingestion.sources import file_input_from_bytes, url_input
from app.services.ingestion.types import IngestionError

router = APIRouter(prefix="/ingestions", tags=["ingestions"])
UploadFileDependency = Annotated[UploadFile, File(...)]


async def _run_ingestion(job_id: UUID, payload) -> None:
    try:
        await IngestionOrchestrator().ingest(job_id, payload)
    except IngestionError:
        return


async def _record_job_failure(job_id: UUID, exc: Exception) -> None:
    async with async_session_factory() as session:
        repo = KnowledgeRepository(session)
        job = await repo.get_job(job_id)
        if job is not None:
            await repo.update_job(
                job,
                status="failed",
                stage="failed",
                progress=100,
                statistics={},
                error={
                    "category": getattr(exc, "category", "unexpected_error"),
                    "message": str(exc),
                    "details": getattr(exc, "safe_details", {}),
                },
            )
            await session.commit()


@router.post(
    "/files", response_model=IngestionAcceptedResponse, status_code=status.HTTP_202_ACCEPTED
)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFileDependency,
    _principal: AdminPrincipal,
):
    chunks: list[bytes] = []
    total = 0
    max_size = get_settings().max_ingestion_file_size_bytes
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > max_size:
            raise HTTPException(status_code=413, detail="File exceeds maximum ingestion size.")
        chunks.append(chunk)
    payload = file_input_from_bytes(
        content=b"".join(chunks),
        filename=file.filename or "uploaded-document",
        content_type=file.content_type,
    )
    orchestrator = IngestionOrchestrator()
    job_id = await orchestrator.create_job()
    background_tasks.add_task(_run_ingestion, job_id, payload)
    return IngestionAcceptedResponse(job_id=job_id, status="queued")


@router.post("/url", response_model=IngestionAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_url(
    background_tasks: BackgroundTasks,
    request: UrlIngestionRequest,
    _principal: AdminPrincipal,
):
    orchestrator = IngestionOrchestrator()
    job_id = await orchestrator.create_job()

    async def fetch_and_ingest() -> None:
        try:
            payload = await url_input(str(request.url))
            await orchestrator.ingest(job_id, payload)
        except IngestionError as exc:
            await _record_job_failure(job_id, exc)
            return

    background_tasks.add_task(fetch_and_ingest)
    return IngestionAcceptedResponse(job_id=job_id, status="queued")


@router.get("/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(
    job_id: UUID,
    _principal: AdminPrincipal,
):
    async with async_session_factory() as session:
        job = await session.get(IngestionJob, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Ingestion job not found.")
        return job
