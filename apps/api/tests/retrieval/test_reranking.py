from uuid import uuid4

import pytest

from app.services.ai.types import RetrievalCandidate, RetrievalFilters, RetrievalQuery
from app.services.retrieval.rerankers import RerankerError
from app.services.retrieval.service import HybridRetriever


class DeterministicEmbeddingProvider:
    active_model = "test-embedding"

    async def embed_query(self, query: str):
        return type("Embedding", (), {"vector": [0.1] * 384, "text": query})()


class FailingReranker:
    async def rerank(self, _query, _candidates):
        raise RerankerError("boom", category="test_failure")


class StaticRepo:
    def __init__(self, *_args):
        self.run_id = uuid4()

    async def vector_candidates(self, **_kwargs):
        return [_candidate(vector_rank=1)]

    async def lexical_candidates(self, **_kwargs):
        return []

    async def persist_run(self, **_kwargs):
        return self.run_id


def _candidate(vector_rank=None):
    return RetrievalCandidate(
        source_id=uuid4(),
        document_id=uuid4(),
        document_version=1,
        chunk_id=uuid4(),
        chunk_position=0,
        title="GroundStack Local Setup",
        source_display_name="setup.md",
        source_uri=None,
        source_type="file",
        section_path=["Database"],
        chunk_content="Database connection failures are visible in the status indicator.",
        chunk_checksum="checksum",
        vector_rank=vector_rank,
        vector_distance=0.1,
    )


@pytest.mark.parametrize("reranking_enabled", [False, True])
async def test_retriever_returns_degraded_mode_when_reranker_fails(
    monkeypatch, reranking_enabled
) -> None:
    from app.core.settings import Settings

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def commit(self):
            return None

    monkeypatch.setattr("app.services.retrieval.service.async_session_factory", lambda: Session())
    monkeypatch.setattr("app.services.retrieval.service.RetrievalRepository", StaticRepo)
    settings = Settings(reranking_enabled=reranking_enabled)
    retriever = HybridRetriever(
        embedding_provider=DeterministicEmbeddingProvider(),
        reranker=FailingReranker(),
        settings=settings,
    )

    result = await retriever.retrieve(
        RetrievalQuery(text="database failing", filters=RetrievalFilters(), limit=3)
    )

    assert result.evidence_found is True
    if reranking_enabled:
        assert result.degraded_mode is not None
        assert result.trace.reranking_mode == "degraded"
    else:
        assert result.degraded_mode is None
        assert result.trace.reranking_mode == "disabled"
