import asyncio

from fastapi import APIRouter

from app.core.settings import get_settings
from app.db.health import check_database
from app.db.session import async_session_factory
from app.schemas.system import (
    DemoAvailabilityResponse,
    EmbeddingStatus,
    HealthResponse,
    KnowledgeCounts,
    LLMStatus,
    ReadinessResponse,
    RerankerStatus,
    RetrievalStatus,
    SystemStatusResponse,
)
from app.services.ai.embeddings import detect_device
from app.services.ai.llm import get_llm_provider
from app.services.ingestion.persistence import KnowledgeRepository
from app.services.operations.demo_limits import demo_availability, redis_connectivity_ok
from app.services.retrieval.repository import RetrievalRepository

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=get_settings().app_name)


@router.get("/health/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    return HealthResponse(status="ok", service=get_settings().app_name)


@router.get("/health/ready", response_model=ReadinessResponse)
async def ready() -> ReadinessResponse:
    settings = get_settings()
    checks: dict[str, str] = {}
    database = await check_database()
    checks["database"] = "ok" if database.connected else "unavailable"
    if settings.demo_redis_required or settings.redis_url:
        checks["redis"] = "ok" if await redis_connectivity_ok() else "unavailable"
    if settings.app_env == "demo":
        try:
            llm = await asyncio.wait_for(get_llm_provider().health(), timeout=1.5)
            checks["inference"] = "ok" if llm.reachable and llm.model_available else "unavailable"
        except Exception:
            checks["inference"] = "unavailable"
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return ReadinessResponse(status=status, checks=checks)


@router.get("/demo/availability", response_model=DemoAvailabilityResponse)
async def public_demo_availability() -> DemoAvailabilityResponse:
    availability = await demo_availability()
    return DemoAvailabilityResponse(
        state=availability.state,
        chat_enabled=availability.chat_enabled,
        reason=availability.reason,
        retry_after_seconds=availability.retry_after_seconds,
    )


@router.get("/system/status", response_model=SystemStatusResponse)
async def system_status() -> SystemStatusResponse:
    settings = get_settings()
    database = await check_database()
    try:
        llm_health = await asyncio.wait_for(get_llm_provider().health(), timeout=1.5)
        llm = LLMStatus(
            **llm_health.model_dump(),
            model_variant=settings.llm_model_variant,
            adapter_name=settings.llm_adapter_name or None,
            adapter_version=settings.llm_adapter_version or None,
            dataset_version=settings.llm_dataset_version or None,
            model_manifest_checksum=settings.llm_model_manifest_checksum or None,
            evaluation_status=settings.llm_evaluation_status,
            promotion_status=settings.llm_promotion_status,
        )
    except Exception as exc:
        llm = LLMStatus(
            provider=settings.llm_provider,
            model=settings.llm_model,
            reachable=False,
            model_available=False,
            loaded=None,
            detail=str(exc) or "LLM provider status check failed.",
            model_variant=settings.llm_model_variant,
            adapter_name=settings.llm_adapter_name or None,
            adapter_version=settings.llm_adapter_version or None,
            dataset_version=settings.llm_dataset_version or None,
            model_manifest_checksum=settings.llm_model_manifest_checksum or None,
            evaluation_status=settings.llm_evaluation_status,
            promotion_status=settings.llm_promotion_status,
        )
    if database.connected:
        async with async_session_factory() as session:
            knowledge_repo = KnowledgeRepository(session)
            retrieval_repo = RetrievalRepository(session)
            counts = await knowledge_repo.counts()
            indexes = await retrieval_repo.index_status()
            searchable = await retrieval_repo.searchable_counts()
    else:
        counts = {
            "knowledge_sources": 0,
            "document_versions": 0,
            "chunks": 0,
            "completed_ingestion_jobs": 0,
            "failed_ingestion_jobs": 0,
        }
        indexes = {"hnsw": False, "gin": False}
        searchable = {"searchable_sources": 0, "searchable_chunks": 0}
    return SystemStatusResponse(
        application="online",
        environment=settings.environment,
        database=database,
        embeddings=EmbeddingStatus(
            provider=settings.embedding_provider,
            model=settings.embedding_model_name,
            dimension=settings.embedding_dimension,
            device=detect_device(settings.embedding_device),
            loaded=False,
        ),
        reranker=RerankerStatus(
            provider=settings.reranker_provider,
            model=settings.reranker_model_name,
            device=detect_device(settings.reranker_device),
            enabled=settings.reranking_enabled,
            loaded=False,
        ),
        retrieval=RetrievalStatus(
            algorithm_version=settings.retrieval_algorithm_version,
            reranking_enabled=settings.reranking_enabled,
            vector_index_available=indexes["hnsw"],
            text_search_index_available=indexes["gin"],
            searchable_sources=searchable["searchable_sources"],
            searchable_chunks=searchable["searchable_chunks"],
        ),
        llm=llm,
        knowledge=KnowledgeCounts(**counts),
    )
