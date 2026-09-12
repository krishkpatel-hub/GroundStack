from time import perf_counter
from typing import Any

import structlog

from app.core.settings import Settings, get_settings
from app.db.session import async_session_factory
from app.services.ai.embeddings import (
    SentenceTransformerEmbeddingProvider,
    get_embedding_provider,
)
from app.services.ai.interfaces import Retriever
from app.services.ai.types import RetrievalQuery, RetrievalResult, RetrievalTrace
from app.services.retrieval.query import prepare_query
from app.services.retrieval.repository import RetrievalRepository
from app.services.retrieval.selection import build_citations, select_relevant_candidates

logger = structlog.get_logger(__name__)


def _ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 3)


class SemanticRetriever(Retriever):
    def __init__(
        self,
        *,
        embedding_provider: SentenceTransformerEmbeddingProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embedding_provider = embedding_provider or get_embedding_provider()

    def configuration_snapshot(self, *, top_k: int) -> dict[str, Any]:
        return {
            "candidate_limit": self.settings.retrieval_candidate_limit,
            "final_top_k": top_k,
            "max_vector_distance": self.settings.retrieval_max_vector_distance,
            "embedding_model": self.settings.embedding_model_name,
        }

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        total_start = perf_counter()
        prepared = prepare_query(query.text, max_length=self.settings.max_retrieval_query_length)
        top_k = min(query.limit, self.settings.retrieval_max_top_k)

        embedding_start = perf_counter()
        embedding = await self.embedding_provider.embed_query(prepared.normalized_text)
        if len(embedding.vector) != self.settings.embedding_dimension:
            raise ValueError("Query embedding dimension mismatch.")
        latency = {"embedding": _ms(embedding_start)}

        async with async_session_factory() as session:
            repo = RetrievalRepository(session)
            search_start = perf_counter()
            candidates = await repo.vector_candidates(
                query_vector=embedding.vector,
                filters=query.filters,
                limit=self.settings.retrieval_candidate_limit,
            )
            latency["vector_search"] = _ms(search_start)
            selected = select_relevant_candidates(
                candidates,
                top_k=top_k,
                max_vector_distance=self.settings.retrieval_max_vector_distance,
            )
            citations = build_citations(selected)
            latency["total"] = _ms(total_start)
            run_id = await repo.persist_run(
                query_text=(
                    prepared.normalized_text if self.settings.persist_retrieval_queries else None
                ),
                query_hash=prepared.query_hash,
                query_length=prepared.query_length,
                applied_filters=query.filters.model_dump(mode="json"),
                configuration=self.configuration_snapshot(top_k=top_k),
                algorithm_version=self.settings.retrieval_algorithm_version,
                candidate_counts={"vector": len(candidates), "final": len(selected)},
                latency_ms=latency,
                candidates=candidates,
            )
            await session.commit()

        trace = RetrievalTrace(
            query_hash=prepared.query_hash,
            query_length=prepared.query_length,
            vector_candidate_count=len(candidates),
            final_result_count=len(selected),
            latency_ms=latency,
        )
        logger.info(
            "retrieval_completed",
            retrieval_run_id=str(run_id),
            query_hash=prepared.query_hash,
            query_length=prepared.query_length,
            vector_candidate_count=len(candidates),
            final_result_count=len(selected),
            embedding_latency_ms=latency["embedding"],
            vector_search_latency_ms=latency["vector_search"],
            total_latency_ms=latency["total"],
        )
        return RetrievalResult(
            retrieval_run_id=run_id,
            normalized_query=prepared.normalized_text,
            result_count=len(citations),
            evidence_found=bool(citations),
            applied_filters=query.filters,
            citations=citations,
            candidates=(
                selected if query.include_debug and self.settings.retrieval_debug_enabled else []
            ),
            trace=trace,
        )
