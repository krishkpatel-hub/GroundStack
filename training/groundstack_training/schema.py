from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

ANSWERABILITY = {"answerable", "insufficient_evidence", "ambiguous"}
PROVENANCE_ORIGINS = {
    "human_authored",
    "human_reviewed_synthetic",
    "approved_application_conversation",
    "imported_licensed_community_data",
}
REVIEW_STATUSES = {"approved", "rejected", "needs_review"}


@dataclass(frozen=True)
class Evidence:
    citation_id: str
    title: str
    section: str
    content: str


@dataclass(frozen=True)
class Provenance:
    origin: str
    license: str
    review_status: str
    source_name: str = "GroundStack seed dataset"
    original_location: str = "training/data/seed"
    collection_method: str = "human authored development examples"
    redistribution_allowed: bool = True
    reviewer: str = "GroundStack maintainer"


@dataclass(frozen=True)
class CanonicalExample:
    example_id: str
    question: str
    evidence: list[Evidence]
    answer: str
    answerability: str
    source_group: str
    category: str
    difficulty: str
    provenance: Provenance
    quality_flags: list[str] = field(default_factory=list)
    created_at: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CanonicalExample:
        evidence = [Evidence(**item) for item in data.get("evidence", [])]
        provenance = Provenance(**data.get("provenance", {}))
        return cls(
            example_id=data["example_id"],
            question=data["question"],
            evidence=evidence,
            answer=data["answer"],
            answerability=data["answerability"],
            source_group=data["source_group"],
            category=data["category"],
            difficulty=data["difficulty"],
            provenance=provenance,
            quality_flags=list(data.get("quality_flags", [])),
            created_at=data.get("created_at", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "example_id": self.example_id,
            "question": self.question,
            "evidence": [item.__dict__ for item in self.evidence],
            "answer": self.answer,
            "answerability": self.answerability,
            "source_group": self.source_group,
            "category": self.category,
            "difficulty": self.difficulty,
            "provenance": self.provenance.__dict__,
            "quality_flags": self.quality_flags,
            "created_at": self.created_at,
        }


def load_jsonl(path: str | Path) -> list[CanonicalExample]:
    examples: list[CanonicalExample] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                examples.append(CanonicalExample.from_dict(json.loads(line)))
            except Exception as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return examples


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def parse_iso8601(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
