from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.orm import selectinload

from app.core.settings import get_settings
from app.db.session import async_session_factory
from app.models.knowledge import RetrievalRun
from app.schemas.retrieval import (
    RetrievalConfigResponse,
    RetrievalRunDetailResponse,
    RetrievalRunResultResponse,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
)
from app.services.ai.types import RetrievalFilters, RetrievalQuery
from app.services.operations.metrics import metrics
from app.services.operations.rate_limit import BackpressureError, gate, limiter
from app.services.retrieval.query import RetrievalValidationError
from app.services.retrieval.service import HybridRetriever

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


def get_retriever() -> HybridRetriever:
    return HybridRetriever()


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    host = forwarded or (request.client.host if request.client else "local")
    return f"retrieval:{host}"


async def _enforce_retrieval_limit(request: Request) -> None:
    settings = get_settings()
    decision = await limiter("retrieval", limit=settings.retrieval_rate_limit_per_minute).check(
        _client_key(request)
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many retrieval requests.",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )


@router.get("/config", response_model=RetrievalConfigResponse)
async def retrieval_config() -> RetrievalConfigResponse:
    settings = get_settings()
    return RetrievalConfigResponse(
        algorithm_version=settings.retrieval_algorithm_version,
        vector_candidate_limit=settings.vector_candidate_limit,
        lexical_candidate_limit=settings.lexical_candidate_limit,
        rrf_k=settings.rrf_k,
        vector_rrf_weight=settings.vector_rrf_weight,
        lexical_rrf_weight=settings.lexical_rrf_weight,
        rerank_candidate_limit=settings.rerank_candidate_limit,
        final_top_k=settings.retrieval_final_top_k,
        max_top_k=settings.retrieval_max_top_k,
        max_chunks_per_source=settings.max_chunks_per_source,
        reranking_enabled=settings.reranking_enabled,
        reranker_provider=settings.reranker_provider,
        reranker_model=settings.reranker_model_name,
        persist_retrieval_queries=settings.persist_retrieval_queries,
        debug_enabled=settings.retrieval_debug_enabled,
    )


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_retrieval(
    request: RetrievalSearchRequest, http_request: Request
) -> RetrievalSearchResponse:
    settings = get_settings()
    await _enforce_retrieval_limit(http_request)
    if request.top_k > settings.retrieval_max_top_k:
        raise HTTPException(status_code=422, detail="top_k exceeds configured maximum.")
    retriever = get_retriever()
    try:
        async with gate(
            "retrieval",
            max_concurrency=settings.retrieval_concurrency,
            timeout_seconds=settings.model_queue_timeout_seconds,
        ).acquire():
            result = await retriever.retrieve(
                RetrievalQuery(
                    text=request.query,
                    limit=request.top_k,
                    filters=RetrievalFilters(
                        source_types=request.filters.source_types,
                        source_ids=request.filters.source_ids,
                        document_ids=request.filters.document_ids,
                    ),
                    include_debug=request.include_debug,
                )
            )
    except BackpressureError as exc:
        metrics.increment("groundstack_backpressure_total", operation="retrieval", result="busy")
        raise HTTPException(status_code=503, detail=str(exc), headers={"Retry-After": "3"}) from exc
    except RetrievalValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": exc.code,
                "message": str(exc),
                "max_length": exc.max_length,
            },
        ) from exc
    return RetrievalSearchResponse(
        retrieval_run_id=result.retrieval_run_id,
        normalized_query=result.normalized_query,
        result_count=result.result_count,
        evidence_found=result.evidence_found,
        reranking_applied=result.reranking_applied,
        degraded_mode=result.degraded_mode,
        applied_filters=result.applied_filters.model_dump(),
        citations=[citation.model_dump() for citation in result.citations],
        timings_ms=result.trace.latency_ms,
        debug=[candidate.model_dump() for candidate in result.candidates] or None,
    )


@router.get("/runs/{retrieval_run_id}", response_model=RetrievalRunDetailResponse)
async def get_retrieval_run(
    retrieval_run_id: UUID,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RetrievalRunDetailResponse:
    async with async_session_factory() as session:
        run = await session.get(
            RetrievalRun,
            retrieval_run_id,
            options=[selectinload(RetrievalRun.results)],
        )
        if run is None:
            raise HTTPException(status_code=404, detail="Retrieval run not found.")
        sorted_results = sorted(
            run.results,
            key=lambda item: (
                item.final_rank if item.final_rank is not None else 10**9,
                not item.selected,
                item.created_at,
            ),
        )
        page = sorted_results[offset : offset + limit]
        return RetrievalRunDetailResponse(
            id=run.id,
            query_text=run.query_text,
            query_hash=run.query_hash,
            query_length=run.query_length,
            applied_filters=run.applied_filters,
            configuration=run.configuration,
            algorithm_version=run.algorithm_version,
            candidate_counts=run.candidate_counts,
            reranking_mode=run.reranking_mode,
            degraded_mode=run.degraded_mode,
            latency_ms=run.latency_ms,
            created_at=run.created_at,
            total=len(sorted_results),
            limit=limit,
            offset=offset,
            results=[
                RetrievalRunResultResponse(
                    chunk_id=item.chunk_id,
                    vector_rank=item.vector_rank,
                    vector_distance=item.vector_distance,
                    lexical_rank=item.lexical_rank,
                    lexical_score=item.lexical_score,
                    rrf_score=item.rrf_score,
                    reranker_score=item.reranker_score,
                    final_rank=item.final_rank,
                    selected=item.selected,
                    exclusion_reason=item.exclusion_reason,
                )
                for item in page
            ],
        )
