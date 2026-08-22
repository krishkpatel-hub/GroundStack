from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from app.db.session import async_session_factory
from app.models.conversation import (
    Conversation,
    EvaluationRun,
    Message,
    MessageFeedback,
    TrainingCandidate,
)
from app.models.knowledge import IngestionJob
from app.services.ai.types import EmbeddingRequest, EmbeddingResult
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.ingestion.sources import file_input_from_path


class DemoEmbeddingProvider:
    active_model = "demo-deterministic-384"

    async def embed(self, request: EmbeddingRequest) -> list[EmbeddingResult]:
        return [
            EmbeddingResult(text=text, vector=[float((index + len(text)) % 7) / 7 for index in range(384)])
            for text in request.inputs
        ]


async def ingest_demo_docs(root: Path) -> None:
    orchestrator = IngestionOrchestrator(embedding_provider=DemoEmbeddingProvider())
    for path in sorted((root / "apps/api/dev-data/knowledge-base").glob("*")):
        job_id = await orchestrator.create_job()
        await orchestrator.ingest(job_id, file_input_from_path(path))


async def seed_records() -> None:
    async with async_session_factory() as session:
        conversation = Conversation(
            title="Demo: pgvector setup",
            owner_subject="demo:standard-user",
            archived=False,
            last_message_at=datetime.now(UTC),
        )
        session.add(conversation)
        await session.flush()
        user = Message(
            conversation_id=conversation.id,
            owner_subject=conversation.owner_subject,
            role="user",
            status="completed",
            content="How do I configure pgvector for GroundStack?",
        )
        assistant = Message(
            conversation_id=conversation.id,
            owner_subject=conversation.owner_subject,
            role="assistant",
            status="completed",
            content=(
                "Use the provided PostgreSQL image with pgvector enabled, run Alembic "
                "migrations, and verify the vector extension before ingestion. [S1]"
            ),
            grounding_status="grounded",
            provider="demo",
            model="demo-deterministic",
            prompt_version="grounded_answer/v1",
        )
        insufficient = Message(
            conversation_id=conversation.id,
            owner_subject=conversation.owner_subject,
            role="assistant",
            status="completed",
            content=(
                "GroundStack does not have enough retrieved evidence to answer that. "
                "Try rephrasing or ask an administrator to add the missing documentation."
            ),
            grounding_status="insufficient_evidence",
            provider="demo",
            model="demo-deterministic",
            prompt_version="grounded_answer/v1",
        )
        session.add_all([user, assistant, insufficient])
        await session.flush()
        feedback = MessageFeedback(
            message_id=assistant.id,
            conversation_id=conversation.id,
            owner_subject=conversation.owner_subject,
            rating="negative",
            categories=["incomplete_answer"],
            comment="Mention migrations explicitly.",
            suggested_correction="Include the migration command and pgvector extension check.",
            citations_incorrect=False,
            reported_citation_ids=[],
            client_request_id="demo-feedback-1",
            message_snapshot={"demo": True},
        )
        session.add(feedback)
        await session.flush()
        session.add(
            TrainingCandidate(
                message_id=assistant.id,
                feedback_id=feedback.id,
                status="pending",
                proposed_question=user.content,
                evidence_snapshot=[{"citation_id": "S1", "demo": True}],
                proposed_answer=feedback.suggested_correction or assistant.content,
                citation_references=["S1"],
                redaction_status="pending",
                provenance_status="pending",
            )
        )
        session.add(
            EvaluationRun(
                name="Demo evaluation run",
                status="completed",
                suite_names=["generation", "prompt_injection"],
                dataset_version="demo-seed-v1",
                dataset_checksum="demo",
                model_metadata={"provider": "demo", "model": "demo-deterministic"},
                prompt_version="grounded_answer/v1",
                retrieval_configuration={"algorithm": "hybrid-rrf-ce-v1"},
                environment_metadata={"report_path": "evaluation/reports/demo-seed.json"},
                aggregate_metrics={"pass_rate": 1.0, "sample_count": 4},
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
        )
        session.add(
            IngestionJob(
                status="failed",
                current_stage="source_validation",
                progress=100,
                statistics={"demo": True},
                error={
                    "category": "demo_validation_failure",
                    "message": "Demo failed job for recovery workflow.",
                },
            )
        )
        await session.commit()


async def main() -> None:
    root = Path(__file__).resolve().parents[1]
    await ingest_demo_docs(root)
    await seed_records()
    print("Demo data seeded: corpus, conversations, feedback, training candidate, evaluation run.")


if __name__ == "__main__":
    asyncio.run(main())
