from __future__ import annotations

import hashlib
from dataclasses import dataclass
from difflib import SequenceMatcher

from groundstack_training.quality import normalized_text
from groundstack_training.schema import CanonicalExample


@dataclass(frozen=True)
class DeduplicationResult:
    retained: list[CanonicalExample]
    rejected: list[dict[str, str]]
    exact_duplicates: int
    near_duplicates: int


def content_hash(example: CanonicalExample) -> str:
    text = "\n".join(
        [
            normalized_text(example.question),
            normalized_text(example.answer),
            *[normalized_text(item.content) for item in example.evidence],
        ]
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def similarity(first: CanonicalExample, second: CanonicalExample) -> float:
    first_text = normalized_text(first.question + "\n" + first.answer)
    second_text = normalized_text(second.question + "\n" + second.answer)
    return SequenceMatcher(a=first_text, b=second_text).ratio()


def deduplicate(
    examples: list[CanonicalExample], *, near_duplicate_threshold: float
) -> DeduplicationResult:
    retained: list[CanonicalExample] = []
    rejected: list[dict[str, str]] = []
    hashes: dict[str, str] = {}
    exact = 0
    near = 0
    for example in sorted(examples, key=lambda item: item.example_id):
        digest = content_hash(example)
        if digest in hashes:
            exact += 1
            rejected.append(
                {
                    "example_id": example.example_id,
                    "reason": "exact_duplicate",
                    "duplicate_of": hashes[digest],
                }
            )
            continue
        near_match = next(
            (
                retained_example
                for retained_example in retained
                if similarity(example, retained_example) >= near_duplicate_threshold
            ),
            None,
        )
        if near_match:
            near += 1
            rejected.append(
                {
                    "example_id": example.example_id,
                    "reason": "near_duplicate",
                    "duplicate_of": near_match.example_id,
                }
            )
            continue
        hashes[digest] = example.example_id
        retained.append(example)
    return DeduplicationResult(retained, rejected, exact, near)
