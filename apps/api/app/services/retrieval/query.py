import hashlib
import re
import unicodedata
from dataclasses import dataclass

from app.core.settings import get_settings


class RetrievalValidationError(ValueError):
    def __init__(self, message: str, *, code: str, max_length: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.max_length = max_length


@dataclass(frozen=True)
class PreparedQuery:
    raw_text: str
    normalized_text: str
    query_hash: str
    query_length: int


_WHITESPACE_RE = re.compile(r"\s+")


def prepare_query(text: str, *, max_length: int | None = None) -> PreparedQuery:
    settings = get_settings()
    configured_max = max_length or settings.max_retrieval_query_length
    normalized = unicodedata.normalize("NFKC", text)
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
    if not normalized:
        raise RetrievalValidationError("Query cannot be empty.", code="empty_query")
    if len(normalized) > configured_max:
        raise RetrievalValidationError(
            "Query is too long.", code="query_too_long", max_length=configured_max
        )
    return PreparedQuery(
        raw_text=text,
        normalized_text=normalized,
        query_hash=hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        query_length=len(normalized),
    )
