from __future__ import annotations

import argparse
import asyncio
import json
from uuid import UUID

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models.conversation import Message, TrainingCandidate
from app.schemas.feedback import clean_text


async def list_candidates(status: str, limit: int) -> int:
    async with async_session_factory() as session:
        rows = await session.execute(
            select(TrainingCandidate, Message)
            .join(Message, Message.id == TrainingCandidate.message_id)
            .where(TrainingCandidate.status == status)
            .order_by(TrainingCandidate.created_at)
            .limit(limit)
        )
        payload = []
        for candidate, message in rows:
            payload.append(
                {
                    "candidate_id": str(candidate.id),
                    "message_id": str(candidate.message_id),
                    "feedback_id": str(candidate.feedback_id) if candidate.feedback_id else None,
                    "status": candidate.status,
                    "redaction_status": candidate.redaction_status,
                    "provenance_status": candidate.provenance_status,
                    "dataset_export_status": candidate.dataset_export_status,
                    "proposed_question": candidate.proposed_question,
                    "proposed_answer_preview": message.content[:500],
                    "citation_references": candidate.citation_references,
                    "created_at": candidate.created_at.isoformat(),
                }
            )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0


async def update_candidate(args: argparse.Namespace) -> int:
    async with async_session_factory() as session:
        candidate = await session.get(TrainingCandidate, UUID(args.candidate_id))
        if candidate is None:
            print("Candidate not found.")
            return 1
        if args.status:
            candidate.status = args.status
        if args.redaction_status:
            candidate.redaction_status = args.redaction_status
        if args.provenance_status:
            candidate.provenance_status = args.provenance_status
        if args.notes is not None:
            candidate.reviewer_notes = clean_text(args.notes)
        if args.reviewer:
            candidate.reviewer_identifier = clean_text(args.reviewer)
        await session.commit()
        print(json.dumps({"candidate_id": args.candidate_id, "status": candidate.status}))
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Review GroundStack training candidates.")
    subcommands = parser.add_subparsers(dest="command")
    list_parser = subcommands.add_parser("list")
    list_parser.add_argument("--status", default="pending")
    list_parser.add_argument("--limit", type=int, default=25)
    update_parser = subcommands.add_parser("update")
    update_parser.add_argument("candidate_id")
    update_parser.add_argument(
        "--status", choices=["pending", "needs_redaction", "approved", "rejected"]
    )
    update_parser.add_argument("--redaction-status", choices=["pending", "approved", "rejected"])
    update_parser.add_argument("--provenance-status", choices=["pending", "approved", "rejected"])
    update_parser.add_argument("--notes")
    update_parser.add_argument("--reviewer")
    args = parser.parse_args()
    if args.command in {None, "list"}:
        return asyncio.run(list_candidates(args.status, args.limit))
    if args.command == "update":
        return asyncio.run(update_candidate(args))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
