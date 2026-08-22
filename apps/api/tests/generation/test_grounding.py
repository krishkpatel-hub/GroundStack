from uuid import uuid4

from app.services.ai.types import (
    Citation,
    RetrievalCandidate,
    RetrievalFilters,
    RetrievalResult,
    RetrievalTrace,
)
from app.services.generation.citations import validate_answer_citations
from app.services.generation.context import build_context
from app.services.generation.prompts import load_prompt_template, render_user_prompt


def _candidate(content: str, rank: int = 1) -> RetrievalCandidate:
    return RetrievalCandidate(
        source_id=uuid4(),
        document_id=uuid4(),
        document_version=1,
        chunk_id=uuid4(),
        chunk_position=rank - 1,
        title="GroundStack Setup",
        source_display_name="setup.md",
        source_uri=None,
        source_type="file",
        section_path=["Install"],
        page_number=None,
        chunk_content=content,
        chunk_checksum=f"checksum-{rank}",
        final_rank=rank,
        selected=True,
    )


def _retrieval(candidates: list[RetrievalCandidate]) -> RetrievalResult:
    citations = [
        Citation(
            citation_id=f"S{index}",
            source_id=candidate.source_id,
            document_id=candidate.document_id,
            document_version=candidate.document_version,
            chunk_id=candidate.chunk_id,
            title=candidate.title,
            source_display_name=candidate.source_display_name,
            source_type=candidate.source_type,
            source_uri=candidate.source_uri,
            section_path="Install",
            page_number=None,
            excerpt=candidate.chunk_content[:180],
            final_rank=index,
        )
        for index, candidate in enumerate(candidates, start=1)
    ]
    return RetrievalResult(
        normalized_query="How do I inspect Postgres?",
        result_count=len(citations),
        evidence_found=bool(citations),
        reranking_applied=False,
        applied_filters=RetrievalFilters(),
        citations=citations,
        candidates=candidates,
        trace=RetrievalTrace(query_hash="hash", query_length=28),
    )


def test_prompt_template_loads_with_stable_checksum() -> None:
    template = load_prompt_template("grounded_answer/v1")
    rendered = render_user_prompt(
        template,
        question="How do I inspect Postgres?",
        history="No previous conversation.",
        sources='<source id="S1">docker compose ps</source>',
    )

    assert template.checksum
    assert "How do I inspect Postgres?" in rendered
    assert "docker compose ps" in rendered


def test_context_builder_includes_ordered_sources_under_budget() -> None:
    candidates = [
        _candidate("Run docker compose ps to inspect services.", rank=1),
        _candidate("Use docker compose logs api for backend logs.", rank=2),
    ]
    context = build_context(
        retrieval=_retrieval(candidates),
        history=[],
        context_window=180,
        max_output_tokens=40,
        system_prompt_tokens=20,
        question_tokens=10,
        max_history_messages=4,
    )

    assert context.included_citation_ids == ["S1", "S2"]
    assert '<source id="S1"' in context.sources_text
    assert "UNTRUSTED SOURCE CONTENT" in context.sources_text


def test_citation_validator_rejects_fabricated_and_malformed_ids() -> None:
    allowed = _retrieval([_candidate("Run docker compose ps.")]).citations
    validation = validate_answer_citations(
        "Use docker compose ps [S1]. Ignore this extra source [S9] and [s1].",
        allowed=allowed,
    )

    assert not validation.valid
    assert validation.fabricated_citation_ids == ["S9"]
    assert validation.malformed
    assert validation.grounding_status == "citation_validation_failed"


def test_citation_validator_requires_citations_for_substantive_answers() -> None:
    allowed = _retrieval([_candidate("Run docker compose ps.")]).citations
    validation = validate_answer_citations(
        "Run docker compose ps to inspect services.",
        allowed=allowed,
    )

    assert not validation.valid
    assert validation.missing_citations
    assert validation.grounding_status == "insufficient_evidence"
