from __future__ import annotations

import re
from dataclasses import dataclass

CITATION_RE = re.compile(r"\[S(\d+)\]")
REFUSAL_RE = re.compile(r"\b(do not have enough|cannot|should not|conflict)\b", re.I)


@dataclass(frozen=True)
class CaseResult:
    test_case_id: str
    suite: str
    category: str
    expected_answerability: str
    deterministic_metrics: dict[str, float | bool]
    passed: bool
    failure_reasons: list[str]


def citation_ids(answer: str) -> list[str]:
    return [f"S{match}" for match in CITATION_RE.findall(answer)]


def evaluate_case(case: dict[str, object]) -> CaseResult:
    answer = str(case.get("response", ""))
    expected = set(case.get("expected_citations", []))
    used = set(citation_ids(answer))
    expected_answerability = str(case.get("expected_answerability", "answerable"))
    failures: list[str] = []
    fabricated = used - expected if expected else used
    missing = expected - used
    if fabricated:
        failures.append("fabricated_citation")
    if missing and expected_answerability == "answerable":
        failures.append("missing_expected_citation")
    refused = bool(REFUSAL_RE.search(answer))
    if expected_answerability == "insufficient_evidence" and not refused:
        failures.append("missing_abstention")
    if expected_answerability == "answerable" and not answer.strip():
        failures.append("empty_answer")
    precision = (len(used & expected) / len(used)) if used else float(not expected)
    recall = (len(used & expected) / len(expected)) if expected else float(not used)
    return CaseResult(
        test_case_id=str(case["id"]),
        suite=str(case.get("suite", "regression")),
        category=str(case.get("category", "general")),
        expected_answerability=expected_answerability,
        deterministic_metrics={
            "citation_precision": round(precision, 4),
            "citation_recall": round(recall, 4),
            "abstained": refused,
            "answer_length": float(len(answer)),
        },
        passed=not failures,
        failure_reasons=failures,
    )
