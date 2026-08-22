from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.conversation import Message, TrainingCandidate


def _canonical_row(candidate: TrainingCandidate, message: Message) -> dict[str, object]:
    evidence = candidate.evidence_snapshot or []
    return {
        "example_id": f"feedback-{candidate.id}",
        "question": candidate.proposed_question,
        "evidence": evidence,
        "answer": candidate.proposed_answer,
        "answerability": "answerable" if evidence else "insufficient_evidence",
        "source_group": "application_feedback",
        "category": "feedback_review",
        "difficulty": "medium",
        "provenance": {
            "origin": "approved_application_conversation",
            "license": "internal-approved-review",
            "review_status": "approved",
            "source_name": "GroundStack conversation feedback",
            "original_location": f"messages/{message.id}",
            "collection_method": "human-reviewed application feedback",
            "redistribution_allowed": True,
            "reviewer": candidate.reviewer_identifier or "GroundStack reviewer",
        },
        "quality_flags": [],
        "created_at": datetime.now(UTC).isoformat(),
    }


async def export(output: Path) -> int:
    async with async_session_factory() as session:
        rows = await session.execute(
            select(TrainingCandidate, Message)
            .join(Message, Message.id == TrainingCandidate.message_id)
            .where(
                TrainingCandidate.status == "approved",
                TrainingCandidate.redaction_status == "approved",
                TrainingCandidate.provenance_status == "approved",
                TrainingCandidate.dataset_export_status != "exported",
            )
            .order_by(TrainingCandidate.created_at)
        )
        selected = list(rows)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for candidate, message in selected:
                handle.write(json.dumps(_canonical_row(candidate, message), sort_keys=True) + "\n")
                candidate.dataset_export_status = "exported"
                candidate.status = "exported"
        await session.commit()
    print(json.dumps({"exported_count": len(selected), "output": str(output)}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Export approved GroundStack training candidates.")
    parser.add_argument("--output", default="training/data/processed/approved_feedback.jsonl")
    args = parser.parse_args()
    return asyncio.run(export(Path(args.output)))


if __name__ == "__main__":
    raise SystemExit(main())
