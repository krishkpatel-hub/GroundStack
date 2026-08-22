from uuid import uuid4

import pytest

from app.services.ai.types import RetrievalCandidate
from app.services.retrieval.fusion import (
    build_citations,
    fuse_candidates,
    select_diverse_candidates,
)
from app.services.retrieval.query import RetrievalValidationError, prepare_query


def candidate(
    *,
    chunk_id=None,
    source_id=None,
    checksum="checksum",
    vector_rank=None,
    lexical_rank=None,
) -> RetrievalCandidate:
    return RetrievalCandidate(
        source_id=source_id or uuid4(),
        document_id=uuid4(),
        document_version=1,
        chunk_id=chunk_id or uuid4(),
        chunk_position=0,
        title="GroundStack Local Setup",
        source_display_name="setup.md",
        source_uri=None,
        source_type="file",
        section_path=["Install"],
        chunk_content="Run docker compose ps to inspect PostgreSQL.",
        chunk_checksum=checksum,
        vector_rank=vector_rank,
        vector_distance=0.2 if vector_rank else None,
        lexical_rank=lexical_rank,
        lexical_score=0.4 if lexical_rank else None,
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


def test_rrf_merges_overlapping_candidates_and_preserves_channel_scores() -> None:
    shared_id = uuid4()
    vector = [candidate(chunk_id=shared_id, vector_rank=1)]
    lexical = [candidate(chunk_id=shared_id, lexical_rank=2), candidate(lexical_rank=1)]

    fused = fuse_candidates(
        vector,
        lexical,
        rrf_k=60,
        vector_weight=1.0,
        lexical_weight=1.0,
    )

    shared = next(item for item in fused if item.chunk_id == shared_id)
    assert len(fused) == 2
    assert shared.vector_rank == 1
    assert shared.lexical_rank == 2
    assert shared.rrf_score == pytest.approx(1 / 61 + 1 / 62)


def test_rrf_weighting_and_tie_breaking_are_deterministic() -> None:
    first = candidate(vector_rank=1)
    second = candidate(lexical_rank=1)

    vector_weighted = fuse_candidates(
        [first],
        [second],
        rrf_k=60,
        vector_weight=2.0,
        lexical_weight=1.0,
    )
    lexical_weighted = fuse_candidates(
        [first],
        [second],
        rrf_k=60,
        vector_weight=1.0,
        lexical_weight=2.0,
    )

    assert vector_weighted[0].chunk_id == first.chunk_id
    assert lexical_weighted[0].chunk_id == second.chunk_id


def test_diversity_removes_duplicates_and_enforces_source_limit() -> None:
    source_id = uuid4()
    candidates = [
        candidate(source_id=source_id, checksum="a", vector_rank=1),
        candidate(source_id=source_id, checksum="a", vector_rank=2),
        candidate(source_id=source_id, checksum="b", vector_rank=3),
    ]

    selected = select_diverse_candidates(candidates, top_k=3, max_chunks_per_source=1)

    assert len(selected) == 1
    assert candidates[1].exclusion_reason == "duplicate_chunk_checksum"
    assert candidates[2].exclusion_reason == "source_limit"


def test_citation_numbering_matches_final_order() -> None:
    candidates = [candidate(vector_rank=1), candidate(vector_rank=2)]
    for index, item in enumerate(candidates, start=1):
        item.final_rank = index

    citations = build_citations(candidates)

    assert [citation.citation_id for citation in citations] == ["S1", "S2"]
    assert citations[0].section_path == "Install"
