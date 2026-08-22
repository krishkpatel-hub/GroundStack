import re
from dataclasses import dataclass

from app.services.ai.types import Citation

_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_CITATION_RE = re.compile(r"\[S(\d+)\]")


@dataclass(frozen=True)
class CitationValidation:
    valid: bool
    used_citation_ids: list[str]
    fabricated_citation_ids: list[str]
    malformed: bool
    missing_citations: bool
    grounding_status: str


def validate_answer_citations(answer: str, allowed: list[Citation]) -> CitationValidation:
    allowed_ids = {citation.citation_id for citation in allowed}
    without_code = _CODE_BLOCK_RE.sub("", answer)
    used = [f"S{match}" for match in _CITATION_RE.findall(without_code)]
    fabricated = sorted({citation_id for citation_id in used if citation_id not in allowed_ids})
    malformed = bool(re.search(r"\[s\d+\]|\[S\]|\[S\d+[^\]]+\]", without_code))
    has_substantive_text = len(re.sub(r"\[[^\]]+\]", "", without_code).strip()) > 40
    missing = has_substantive_text and not used
    valid = not fabricated and not malformed and not missing
    if valid:
        status = "grounded"
    elif fabricated or malformed:
        status = "citation_validation_failed"
    else:
        status = "insufficient_evidence"
    return CitationValidation(
        valid=valid,
        used_citation_ids=used,
        fabricated_citation_ids=fabricated,
        malformed=malformed,
        missing_citations=missing,
        grounding_status=status,
    )
