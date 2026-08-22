from __future__ import annotations

import re
from urllib.parse import urlparse

from groundstack_training.schema import CanonicalExample

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?[\w\-]{8,}"),
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]
PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
]
PRIVATE_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254"}
CITATION_RE = re.compile(r"\[S(\d+)\]")


def normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def citation_ids_in_answer(answer: str) -> list[str]:
    return [f"S{match}" for match in CITATION_RE.findall(answer)]


def quality_flags(example: CanonicalExample) -> list[str]:
    text = "\n".join(
        [example.question, example.answer, *[evidence.content for evidence in example.evidence]]
    )
    flags: list[str] = []
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        flags.append("contains_secret_pattern")
    if any(pattern.search(text) for pattern in PII_PATTERNS):
        flags.append("contains_pii_pattern")
    for token in text.split():
        parsed = urlparse(token.strip("()[]{}<>,"))
        if parsed.scheme in {"http", "https"} and parsed.hostname in PRIVATE_HOSTS:
            flags.append("contains_unsafe_url")
            break
    try:
        text.encode("utf-8").decode("utf-8")
    except UnicodeError:
        flags.append("broken_unicode")
    return sorted(set(flags))
