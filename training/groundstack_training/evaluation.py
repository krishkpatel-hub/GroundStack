from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from groundstack_training.quality import citation_ids_in_answer


@dataclass(frozen=True)
class EvaluationResult:
    metrics: dict[str, float]
    rows: list[dict[str, Any]]


def score_response(example: dict[str, Any], response: str) -> dict[str, Any]:
    allowed = set(example.get("allowed_citation_ids", []))
    used = set(citation_ids_in_answer(response))
    required_facts = list(example.get("required_key_facts", []))
    forbidden = list(example.get("forbidden_claims", []))
    exact = list(example.get("required_exact_strings", []))
    lower = response.casefold()
    return {
        "example_id": example["example_id"],
        "citation_valid": used.issubset(allowed),
        "citation_present": bool(used),
        "citation_coverage": len(used & allowed) / len(allowed) if allowed else 1.0,
        "required_fact_coverage": (
            sum(1 for fact in required_facts if fact.casefold() in lower) / len(required_facts)
            if required_facts
            else 1.0
        ),
        "forbidden_claim": any(claim.casefold() in lower for claim in forbidden),
        "exact_command_preserved": all(item in response for item in exact),
        "refusal": bool(re.search(r"\b(do not have enough|insufficient|cannot answer)\b", lower)),
        "clarification": "clarify" in lower or "which" in lower,
        "output_length": len(response),
    }


def aggregate_scores(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {}
    count = len(rows)
    boolean_fields = [
        "citation_valid",
        "citation_present",
        "forbidden_claim",
        "exact_command_preserved",
        "refusal",
        "clarification",
    ]
    metrics = {
        f"{field}_rate": sum(1 for row in rows if row[field]) / count for field in boolean_fields
    }
    metrics["citation_coverage"] = sum(row["citation_coverage"] for row in rows) / count
    metrics["required_fact_coverage"] = sum(row["required_fact_coverage"] for row in rows) / count
    metrics["mean_output_length"] = sum(row["output_length"] for row in rows) / count
    return metrics


def evaluate_responses(
    examples: list[dict[str, Any]], responses: dict[str, str]
) -> EvaluationResult:
    rows = [
        score_response(example, responses.get(example["example_id"], "")) for example in examples
    ]
    return EvaluationResult(metrics=aggregate_scores(rows), rows=rows)
