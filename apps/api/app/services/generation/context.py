from dataclasses import dataclass

from app.services.ai.types import ChatMessage, RetrievalResult


class ApproximateTokenCounter:
    mode = "approximate"

    def count(self, text: str) -> int:
        return max(1, (len(text) + 3) // 4)


@dataclass(frozen=True)
class ContextBundle:
    sources_text: str
    history_text: str
    included_citation_ids: list[str]
    excluded_citation_ids: list[str]
    token_count: int
    remaining_output_budget: int
    truncation: dict[str, object]
    token_counting_mode: str


def _truncate_preserving_code(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    cut = text[:max_chars].rstrip()
    if cut.count("```") % 2 == 1:
        fence_start = cut.rfind("```")
        if fence_start > max_chars * 0.55:
            cut = cut[:fence_start].rstrip()
    return f"{cut}\n[truncated]", True


def build_context(
    *,
    retrieval: RetrievalResult,
    history: list[ChatMessage],
    context_window: int,
    max_output_tokens: int,
    system_prompt_tokens: int,
    question_tokens: int,
    max_history_messages: int,
) -> ContextBundle:
    counter = ApproximateTokenCounter()
    budget = max(256, context_window - max_output_tokens - system_prompt_tokens - question_tokens)
    recent_history = history[-max_history_messages:] if max_history_messages else []
    history_lines = [
        f"{message.role}: {_truncate_preserving_code(message.content, 900)[0]}"
        for message in recent_history
    ]
    history_text = "\n".join(history_lines) or "No prior conversation."
    used = counter.count(history_text)
    source_parts: list[str] = []
    included: list[str] = []
    excluded: list[str] = []
    truncation: dict[str, object] = {"sources_truncated": []}
    for citation in retrieval.citations:
        chunk = next(
            (
                candidate.chunk_content
                for candidate in retrieval.candidates
                if candidate.chunk_id == citation.chunk_id
            ),
            citation.excerpt,
        )
        header = (
            f'<source id="{citation.citation_id}" title="{citation.title}" '
            f'section="{citation.section_path or ""}" type="{citation.source_type}">'
        )
        footer = "</source>"
        remaining_tokens = budget - used
        if remaining_tokens <= 80:
            excluded.append(citation.citation_id)
            continue
        max_chars = remaining_tokens * 4
        body, was_truncated = _truncate_preserving_code(chunk, max_chars)
        block = f"{header}\nUNTRUSTED SOURCE CONTENT\n{body}\n{footer}"
        block_tokens = counter.count(block)
        if used + block_tokens > budget and source_parts:
            excluded.append(citation.citation_id)
            continue
        source_parts.append(block)
        included.append(citation.citation_id)
        used += block_tokens
        if was_truncated:
            truncation["sources_truncated"].append(citation.citation_id)  # type: ignore[index]
    return ContextBundle(
        sources_text="\n\n".join(source_parts) or "No retrieved evidence.",
        history_text=history_text,
        included_citation_ids=included,
        excluded_citation_ids=excluded,
        token_count=used,
        remaining_output_budget=max_output_tokens,
        truncation=truncation,
        token_counting_mode=counter.mode,
    )
