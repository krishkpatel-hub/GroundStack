from uuid import uuid4

import pytest

from app.services.ai.types import RetrievalCandidate, RetrievalFilters, RetrievalQuery
from app.services.retrieval.query import RetrievalValidationError, prepare_query
from app.services.retrieval.selection import (
    build_citations,
    excerpt_text,
    select_relevant_candidates,
)
from app.services.retrieval.service import SemanticRetriever


def candidate(*, distance: float, content: str = "Resolve GS-DEMO-217 by refreshing config."):
    return RetrievalCandidate(
        source_id=uuid4(),
        document_id=uuid4(),
        document_version=1,
        chunk_id=uuid4(),
        chunk_position=0,
        title="Presentation Validation",
        source_display_name="validation.md",
        source_uri=None,
        source_type="file",
        section_path=["Resolution"],
        chunk_content=content,
        chunk_checksum=str(uuid4()),
        vector_rank=1,
        vector_distance=distance,
    )


def test_prepare_query_normalizes_whitespace_and_hashes() -> None:
    prepared = prepare_query("  Why\tis\nDATABASE_URL failing?  ")

    assert prepared.normalized_text == "Why is DATABASE_URL failing?"
    assert prepared.query_length == len(prepared.normalized_text)
    assert len(prepared.query_hash) == 64


def test_prepare_query_rejects_empty_and_long_queries() -> None:
    with pytest.raises(RetrievalValidationError) as empty:
        prepare_query("   ")
    assert empty.value.code == "empty_query"

    with pytest.raises(RetrievalValidationError) as long_query:
        prepare_query("x" * 6, max_length=5)
    assert long_query.value.code == "query_too_long"


def test_semantic_threshold_and_top_k_bound_evidence() -> None:
    first = candidate(distance=0.20)
    second = candidate(distance=0.30)
    unrelated = candidate(distance=0.70, content="An unrelated policy section.")

    selected = select_relevant_candidates(
        [first, second, unrelated], top_k=1, max_vector_distance=0.45
    )

    assert selected == [first]
    assert first.final_rank == 1
    assert second.exclusion_reason == "below_final_cut"
    assert unrelated.exclusion_reason == "below_relevance_threshold"


def test_citation_numbering_matches_selected_order() -> None:
    candidates = [candidate(distance=0.2), candidate(distance=0.3)]
    select_relevant_candidates(candidates, top_k=2, max_vector_distance=0.45)

    citations = build_citations(candidates)

    assert [citation.citation_id for citation in citations] == ["S1", "S2"]
    assert citations[0].section_path == "Resolution"


def test_excerpt_preserves_procedure_context_for_inspection() -> None:
    text = "Cause. " + "Resolution step. " * 100

    excerpt = excerpt_text(text)

    assert len(excerpt) <= 1203
    assert "Resolution step." in excerpt


class DeterministicEmbeddingProvider:
    active_model = "test-embedding"

    async def embed_query(self, query: str):
        return type("Embedding", (), {"vector": [0.1] * 384, "text": query})()


class StaticRepo:
    def __init__(self, *_args):
        self.run_id = uuid4()

    async def vector_candidates(self, **_kwargs):
        return [candidate(distance=0.2)]

    async def persist_run(self, **_kwargs):
        return self.run_id


async def test_semantic_retriever_returns_thresholded_vector_evidence(monkeypatch) -> None:
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
    retriever = SemanticRetriever(
        embedding_provider=DeterministicEmbeddingProvider(), settings=Settings()
    )

    result = await retriever.retrieve(
        RetrievalQuery(text="How do I resolve GS-DEMO-217?", filters=RetrievalFilters())
    )

    assert result.evidence_found is True
    assert result.trace.vector_candidate_count == 1
    assert result.trace.final_result_count == 1
