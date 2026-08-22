from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from groundstack_training.quality import citation_ids_in_answer, quality_flags
from groundstack_training.schema import (
    ANSWERABILITY,
    PROVENANCE_ORIGINS,
    REVIEW_STATUSES,
    CanonicalExample,
    parse_iso8601,
)


@dataclass(frozen=True)
class ValidationIssue:
    example_id: str
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    accepted_count: int
    rejected_count: int
    issues: list[ValidationIssue]
    answerability_distribution: dict[str, int]
    category_distribution: dict[str, int]
    provenance_distribution: dict[str, int]


def validate_examples(
    examples: list[CanonicalExample],
    *,
    max_input_chars: int = 12000,
    max_output_chars: int = 2400,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    ids: set[str] = set()
    rejected_ids: set[str] = set()

    def reject(example: CanonicalExample, code: str, message: str) -> None:
        rejected_ids.add(example.example_id)
        issues.append(ValidationIssue(example.example_id, "error", code, message))

    for example in examples:
        if not example.example_id or example.example_id in ids:
            reject(example, "duplicate_or_empty_id", "Example IDs must be stable and unique.")
        ids.add(example.example_id)
        if not example.question.strip():
            reject(example, "empty_question", "Question is required.")
        if not example.answer.strip():
            reject(example, "empty_answer", "Answer is required.")
        if example.answerability not in ANSWERABILITY:
            reject(example, "invalid_answerability", "Unsupported answerability label.")
        if example.provenance.origin not in PROVENANCE_ORIGINS:
            reject(example, "invalid_provenance_origin", "Unsupported provenance origin.")
        if example.provenance.review_status not in REVIEW_STATUSES:
            reject(example, "invalid_review_status", "Unsupported review status.")
        if example.provenance.review_status != "approved":
            reject(example, "unapproved_example", "Only approved examples may enter training.")
        if not example.provenance.license or not example.provenance.redistribution_allowed:
            reject(
                example, "unknown_rights", "Known license and redistribution rights are required."
            )
        if example.answerability == "answerable" and not example.evidence:
            reject(example, "missing_evidence", "Answerable examples require evidence.")
        evidence_ids = {item.citation_id for item in example.evidence}
        answer_ids = set(citation_ids_in_answer(example.answer))
        fabricated = answer_ids - evidence_ids
        if fabricated:
            reject(
                example,
                "fabricated_citation",
                f"Answer cites unavailable IDs: {sorted(fabricated)}",
            )
        if example.answerability == "answerable" and not answer_ids:
            reject(example, "missing_citation", "Answerable examples require inline citations.")
        if (
            len(example.question) + sum(len(item.content) for item in example.evidence)
            > max_input_chars
        ):
            reject(example, "input_too_long", "Question plus evidence exceeds maximum length.")
        if len(example.answer) > max_output_chars:
            reject(example, "output_too_long", "Answer exceeds maximum length.")
        for flag in quality_flags(example):
            reject(example, flag, f"Quality screen failed: {flag}.")
        if example.created_at and not parse_iso8601(example.created_at):
            reject(example, "invalid_created_at", "created_at must be ISO-8601.")

    return ValidationReport(
        valid=not any(issue.severity == "error" for issue in issues),
        accepted_count=len(
            [example for example in examples if example.example_id not in rejected_ids]
        ),
        rejected_count=len(rejected_ids),
        issues=issues,
        answerability_distribution=dict(Counter(example.answerability for example in examples)),
        category_distribution=dict(Counter(example.category for example in examples)),
        provenance_distribution=dict(Counter(example.provenance.origin for example in examples)),
    )
