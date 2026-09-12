from app.services.ai.types import Citation, RetrievalCandidate


def select_relevant_candidates(
    candidates: list[RetrievalCandidate], *, top_k: int, max_vector_distance: float
) -> list[RetrievalCandidate]:
    selected: list[RetrievalCandidate] = []
    for candidate in candidates:
        if candidate.vector_distance is None or candidate.vector_distance > max_vector_distance:
            candidate.exclusion_reason = "below_relevance_threshold"
            continue
        if len(selected) >= top_k:
            candidate.exclusion_reason = "below_final_cut"
            continue
        candidate.selected = True
        candidate.final_rank = len(selected) + 1
        candidate.exclusion_reason = None
        selected.append(candidate)
    return selected


def excerpt_text(text: str, *, max_length: int = 1200) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_length:
        return clean
    cut = clean[:max_length].rstrip()
    boundary = max(cut.rfind(" "), cut.rfind("."), cut.rfind("`"))
    if boundary >= max_length * 0.72:
        cut = cut[:boundary].rstrip()
    return f"{cut}..."


def build_citations(candidates: list[RetrievalCandidate]) -> list[Citation]:
    return [
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
            section_path=(" > ".join(candidate.section_path) if candidate.section_path else None),
            page_number=candidate.page_number,
            excerpt=excerpt_text(candidate.chunk_content),
            final_rank=index,
        )
        for index, candidate in enumerate(candidates, start=1)
    ]
