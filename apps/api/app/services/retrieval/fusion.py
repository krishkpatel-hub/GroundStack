from collections import defaultdict

from app.services.ai.types import Citation, RetrievalCandidate


def fuse_candidates(
    vector_candidates: list[RetrievalCandidate],
    lexical_candidates: list[RetrievalCandidate],
    *,
    rrf_k: int,
    vector_weight: float,
    lexical_weight: float,
) -> list[RetrievalCandidate]:
    merged: dict[str, RetrievalCandidate] = {}
    for candidate in vector_candidates:
        merged[str(candidate.chunk_id)] = candidate.model_copy(deep=True)
    for candidate in lexical_candidates:
        key = str(candidate.chunk_id)
        if key not in merged:
            merged[key] = candidate.model_copy(deep=True)
            continue
        current = merged[key]
        current.lexical_rank = candidate.lexical_rank
        current.lexical_score = candidate.lexical_score

    fused = list(merged.values())
    for candidate in fused:
        score = 0.0
        if candidate.vector_rank is not None:
            score += vector_weight / (rrf_k + candidate.vector_rank)
        if candidate.lexical_rank is not None:
            score += lexical_weight / (rrf_k + candidate.lexical_rank)
        candidate.rrf_score = score
    return sorted(
        fused,
        key=lambda item: (
            -(item.rrf_score or 0.0),
            item.vector_rank if item.vector_rank is not None else 10**9,
            item.lexical_rank if item.lexical_rank is not None else 10**9,
            item.title,
            item.chunk_position,
            str(item.chunk_id),
        ),
    )


def select_diverse_candidates(
    candidates: list[RetrievalCandidate],
    *,
    top_k: int,
    max_chunks_per_source: int,
) -> list[RetrievalCandidate]:
    selected: list[RetrievalCandidate] = []
    source_counts: defaultdict[str, int] = defaultdict(int)
    selected_checksums: set[str] = set()
    selected_sections: set[tuple[str, str]] = set()

    for candidate in candidates:
        source_key = str(candidate.source_id)
        section_key = (source_key, " / ".join(candidate.section_path))
        if candidate.chunk_checksum in selected_checksums:
            candidate.exclusion_reason = "duplicate_chunk_checksum"
            continue
        if source_counts[source_key] >= max_chunks_per_source:
            candidate.exclusion_reason = "source_limit"
            continue
        if (
            len(selected) >= max(1, top_k // 2)
            and section_key in selected_sections
            and len(selected) + 1 < top_k
        ):
            candidate.exclusion_reason = "similar_section_deferred"
            continue
        candidate.selected = True
        candidate.final_rank = len(selected) + 1
        candidate.exclusion_reason = None
        selected.append(candidate)
        selected_checksums.add(candidate.chunk_checksum)
        selected_sections.add(section_key)
        source_counts[source_key] += 1
        if len(selected) >= top_k:
            break

    for candidate in candidates:
        if not candidate.selected and candidate.exclusion_reason is None:
            candidate.exclusion_reason = "below_final_cut"
    return selected


def excerpt_text(text: str, *, max_length: int = 420) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_length:
        return clean
    cut = clean[:max_length].rstrip()
    boundary = max(cut.rfind(" "), cut.rfind("."), cut.rfind("`"))
    if boundary >= max_length * 0.72:
        cut = cut[:boundary].rstrip()
    return f"{cut}..."


def build_citations(candidates: list[RetrievalCandidate]) -> list[Citation]:
    citations: list[Citation] = []
    for index, candidate in enumerate(candidates, start=1):
        citations.append(
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
                section_path=" > ".join(candidate.section_path) if candidate.section_path else None,
                page_number=candidate.page_number,
                excerpt=excerpt_text(candidate.chunk_content),
                final_rank=index,
            )
        )
    return citations
