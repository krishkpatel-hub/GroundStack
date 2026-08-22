from time import perf_counter
from typing import Any

import structlog

from app.core.settings import Settings, get_settings
from app.db.session import async_session_factory
from app.services.ai.embeddings import SentenceTransformerEmbeddingProvider, get_embedding_provider
from app.services.ai.interfaces import Retriever
from app.services.ai.types import (
    RetrievalQuery,
    RetrievalResult,
    RetrievalTrace,
)
from app.services.retrieval.fusion import (
    build_citations,
    fuse_candidates,
    select_diverse_candidates,
)
from app.services.retrieval.query import prepare_query
from app.services.retrieval.repository import RetrievalRepository
from app.services.retrieval.rerankers import (
    RerankerError,
    SentenceTransformerReranker,
    get_reranker,
)

logger = structlog.get_logger(__name__)


def _ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 3)


class HybridRetriever(Retriever):
    def __init__(
        self,
        *,
        embedding_provider: SentenceTransformerEmbeddingProvider | None = None,
        reranker: SentenceTransformerReranker | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.reranker = reranker or get_reranker()

    def configuration_snapshot(self, *, top_k: int) -> dict[str, Any]:
        return {
            "vector_candidate_limit": self.settings.vector_candidate_limit,
            "lexical_candidate_limit": self.settings.lexical_candidate_limit,
            "rrf_k": self.settings.rrf_k,
            "vector_rrf_weight": self.settings.vector_rrf_weight,
            "lexical_rrf_weight": self.settings.lexical_rrf_weight,
            "rerank_candidate_limit": self.settings.rerank_candidate_limit,
            "retrieval_final_top_k": top_k,
            "max_chunks_per_source": self.settings.max_chunks_per_source,
            "reranking_enabled": self.settings.reranking_enabled,
            "embedding_model": self.settings.embedding_model_name,
            "reranker_model": self.settings.reranker_model_name,
        }

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        total_start = perf_counter()
        prepared = prepare_query(query.text, max_length=self.settings.max_retrieval_query_length)
        top_k = min(query.limit, self.settings.retrieval_max_top_k)
        latency: dict[str, float] = {}
        degraded_mode: dict[str, str] | None = None
        reranking_mode = "disabled"
        reranking_applied = False

        embedding_start = perf_counter()
        embedding = await self.embedding_provider.embed_query(prepared.normalized_text)
        if len(embedding.vector) != self.settings.embedding_dimension:
            raise ValueError("Query embedding dimension mismatch.")
        latency["embedding"] = _ms(embedding_start)

        async with async_session_factory() as session:
            repo = RetrievalRepository(session)

            vector_start = perf_counter()
            vector_candidates = await repo.vector_candidates(
                query_vector=embedding.vector,
                filters=query.filters,
                limit=self.settings.vector_candidate_limit,
            )
            latency["vector_search"] = _ms(vector_start)

            lexical_start = perf_counter()
            lexical_candidates = await repo.lexical_candidates(
                query_text=prepared.normalized_text,
                filters=query.filters,
                limit=self.settings.lexical_candidate_limit,
            )
            latency["lexical_search"] = _ms(lexical_start)

            fusion_start = perf_counter()
            fused = fuse_candidates(
                vector_candidates,
                lexical_candidates,
                rrf_k=self.settings.rrf_k,
                vector_weight=self.settings.vector_rrf_weight,
                lexical_weight=self.settings.lexical_rrf_weight,
            )
            rerank_input = fused[: self.settings.rerank_candidate_limit]
            latency["fusion"] = _ms(fusion_start)

            rerank_start = perf_counter()
            if self.settings.reranking_enabled and rerank_input:
                try:
                    reranked = await self.reranker.rerank(
                        query.model_copy(update={"text": prepared.normalized_text}), rerank_input
                    )
                    reranking_applied = True
                    reranking_mode = "enabled"
                except RerankerError as exc:
                    degraded_mode = {
                        "stage": "reranking",
                        "reason": exc.category,
                        "message": "Reranking failed; fused RRF order was used.",
                    }
                    reranked = rerank_input
                    reranking_mode = "degraded"
                    logger.warning(
                        "retrieval_reranker_degraded",
                        query_hash=prepared.query_hash,
                        query_length=prepared.query_length,
                        failure_category=exc.category,
                    )
            else:
                reranked = rerank_input
            latency["reranking"] = _ms(rerank_start)

            selection_start = perf_counter()
            selected = select_diverse_candidates(
                reranked,
                top_k=top_k,
                max_chunks_per_source=self.settings.max_chunks_per_source,
            )
            citations = build_citations(selected)
            latency["selection"] = _ms(selection_start)
            latency["total"] = _ms(total_start)

            reranked_ids = {candidate.chunk_id for candidate in reranked}
            all_candidates = reranked + [
                candidate for candidate in fused if candidate.chunk_id not in reranked_ids
            ]
            candidate_counts = {
                "vector": len(vector_candidates),
                "lexical": len(lexical_candidates),
                "fused": len(fused),
                "reranked": len(reranked),
                "final": len(selected),
            }
            run_id = await repo.persist_run(
                query_text=(
                    prepared.normalized_text if self.settings.persist_retrieval_queries else None
                ),
                query_hash=prepared.query_hash,
                query_length=prepared.query_length,
                applied_filters=query.filters.model_dump(mode="json"),
                configuration=self.configuration_snapshot(top_k=top_k),
                algorithm_version=self.settings.retrieval_algorithm_version,
                candidate_counts=candidate_counts,
                reranking_mode=reranking_mode,
                degraded_mode=degraded_mode,
                latency_ms=latency,
                candidates=all_candidates,
            )
            await session.commit()

        trace = RetrievalTrace(
            query_hash=prepared.query_hash,
            query_length=prepared.query_length,
            vector_candidate_count=len(vector_candidates),
            lexical_candidate_count=len(lexical_candidates),
            fused_candidate_count=len(fused),
            reranked_candidate_count=len(reranked),
            final_result_count=len(selected),
            reranking_applied=reranking_applied,
            reranking_mode=reranking_mode,
            degraded_mode=degraded_mode,
            latency_ms=latency,
        )
        logger.info(
            "retrieval_completed",
            retrieval_run_id=str(run_id),
            query_hash=prepared.query_hash,
            query_length=prepared.query_length,
            filter_count=sum(
                [
                    len(query.filters.source_types),
                    len(query.filters.source_ids),
                    len(query.filters.document_ids),
                ]
            ),
            vector_candidate_count=len(vector_candidates),
            lexical_candidate_count=len(lexical_candidates),
            fused_candidate_count=len(fused),
            reranked_candidate_count=len(reranked),
            final_result_count=len(selected),
            embedding_latency_ms=latency["embedding"],
            vector_search_latency_ms=latency["vector_search"],
            lexical_search_latency_ms=latency["lexical_search"],
            fusion_latency_ms=latency["fusion"],
            reranking_latency_ms=latency["reranking"],
            total_latency_ms=latency["total"],
            degraded_mode_reason=degraded_mode["reason"] if degraded_mode else None,
        )
        return RetrievalResult(
            retrieval_run_id=run_id,
            normalized_query=prepared.normalized_text,
            result_count=len(citations),
            evidence_found=bool(citations),
            reranking_applied=reranking_applied,
            degraded_mode=degraded_mode,
            applied_filters=query.filters,
            citations=citations,
            candidates=(
                selected if query.include_debug and self.settings.retrieval_debug_enabled else []
            ),
            trace=trace,
        )
