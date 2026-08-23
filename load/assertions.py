from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

VALID_GROUNDING_STATES = {
    "fully_grounded",
    "partially_grounded",
    "insufficient_evidence",
    "citation_validation_failed",
    "retrieval_failed",
    "generation_failed",
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str = ""


def validate_retrieval_response(payload: dict[str, Any]) -> ValidationResult:
    if "query" not in payload and "normalized_query" not in payload:
        return ValidationResult(False, "missing query field")
    citations = payload.get("citations")
    if citations is not None and not isinstance(citations, list):
        return ValidationResult(False, "citations must be a list")
    for citation in citations or []:
        if not isinstance(citation, dict):
            return ValidationResult(False, "citation must be an object")
        if not (citation.get("citation_id") and citation.get("title")):
            return ValidationResult(False, "citation missing citation_id or title")
    return ValidationResult(True)


def parse_sse(body: bytes) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    current_event = "message"
    for raw_line in body.decode("utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if line.startswith("event:"):
            current_event = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data = line.removeprefix("data:").strip()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"raw": data}
            events.append((current_event, payload))
    return events


def validate_chat_stream(body: bytes) -> ValidationResult:
    events = parse_sse(body)
    if not events:
        return ValidationResult(False, "empty stream")
    terminal = [event for event, _payload in events if event in {"completed", "error"}]
    if not terminal:
        return ValidationResult(False, "stream missing terminal event")
    canonical = [payload for event, payload in events if event == "canonical_answer"]
    if terminal[-1] == "completed" and not canonical:
        return ValidationResult(False, "completed stream missing canonical answer")
    for payload in canonical:
        if not payload.get("request_id"):
            return ValidationResult(False, "canonical answer missing request_id")
        grounding = str(payload.get("grounding_status") or "")
        if grounding not in VALID_GROUNDING_STATES:
            return ValidationResult(False, f"invalid grounding state {grounding}")
        citations = payload.get("citations", [])
        if not isinstance(citations, list):
            return ValidationResult(False, "citations must be a list")
    return ValidationResult(True)


def validate_discord_response(payload: dict[str, Any]) -> ValidationResult:
    if payload.get("type") not in {1, 4, 5}:
        return ValidationResult(False, "unexpected Discord response type")
    data = payload.get("data") or {}
    allowed_mentions = data.get("allowed_mentions")
    if allowed_mentions and allowed_mentions != {"parse": []}:
        return ValidationResult(False, "Discord response allows mentions")
    return ValidationResult(True)
