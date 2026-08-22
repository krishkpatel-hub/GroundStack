import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_last_message_at", "last_message_at"),
        Index("ix_conversations_archived", "archived"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(200))
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    owner_subject: Mapped[str | None] = mapped_column(String(200))
    demo_session_id: Mapped[str | None] = mapped_column(String(120))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "client_request_id", name="uq_messages_client_request"),
        Index("ix_messages_generation_run_id", "generation_run_id"),
        Index("ix_messages_retrieval_run_id", "retrieval_run_id"),
        Index("ix_messages_owner_subject", "owner_subject"),
        Index("ix_messages_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    owner_subject: Mapped[str | None] = mapped_column(String(200))
    grounding_status: Mapped[str | None] = mapped_column(String(64))
    retrieval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retrieval_runs.id", ondelete="SET NULL")
    )
    generation_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    provider: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(200))
    prompt_version: Mapped[str | None] = mapped_column(String(120))
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    failure: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    client_request_id: Mapped[str | None] = mapped_column(String(120))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class GenerationRun(Base):
    __tablename__ = "generation_runs"
    __table_args__ = (
        Index("ix_generation_runs_conversation_id", "conversation_id"),
        Index("ix_generation_runs_message_id", "message_id"),
        Index("ix_generation_runs_retrieval_run_id", "retrieval_run_id"),
        Index("ix_generation_runs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )
    retrieval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retrieval_runs.id", ondelete="SET NULL")
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    generation_parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    context_citation_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    context_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_counting_mode: Mapped[str] = mapped_column(
        String(40), nullable=False, default="approximate"
    )
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    first_token_latency_ms: Mapped[float | None] = mapped_column(Float)
    total_latency_ms: Mapped[float | None] = mapped_column(Float)
    finish_reason: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    repair_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    rendered_prompt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MessageCitation(Base):
    __tablename__ = "message_citations"
    __table_args__ = (
        UniqueConstraint("message_id", "citation_id", name="uq_message_citation_id"),
        UniqueConstraint("message_id", "chunk_id", name="uq_message_citation_chunk"),
        Index("ix_message_citations_message_id", "message_id"),
        Index("ix_message_citations_chunk_id", "chunk_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False
    )
    citation_id: Mapped[str] = mapped_column(String(16), nullable=False)
    citation_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MessageFeedback(Base):
    __tablename__ = "message_feedback"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "client_request_id", name="uq_message_feedback_message_client"
        ),
        Index("ix_message_feedback_conversation_id", "conversation_id"),
        Index("ix_message_feedback_owner_subject", "owner_subject"),
        Index("ix_message_feedback_rating", "rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[str] = mapped_column(String(16), nullable=False)
    owner_subject: Mapped[str | None] = mapped_column(String(200))
    demo_session_id: Mapped[str | None] = mapped_column(String(120))
    categories: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    comment: Mapped[str | None] = mapped_column(String(1000))
    suggested_correction: Mapped[str | None] = mapped_column(String(3000))
    citations_incorrect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reported_citation_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    client_request_id: Mapped[str] = mapped_column(String(120), nullable=False)
    message_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TrainingCandidate(Base):
    __tablename__ = "training_candidates"
    __table_args__ = (
        UniqueConstraint(
            "message_id", "feedback_id", name="uq_training_candidate_message_feedback"
        ),
        Index("ix_training_candidates_status", "status"),
        Index("ix_training_candidates_message_id", "message_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    feedback_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("message_feedback.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    proposed_question: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    proposed_answer: Mapped[str] = mapped_column(Text, nullable=False)
    citation_references: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    redaction_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    provenance_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    reviewer_notes: Mapped[str | None] = mapped_column(String(2000))
    reviewer_identifier: Mapped[str | None] = mapped_column(String(120))
    dataset_export_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="not_exported"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_evaluation_runs_status", "status"),
        Index("ix_evaluation_runs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    suite_names: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    dataset_version: Mapped[str] = mapped_column(String(120), nullable=False)
    dataset_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    model_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    prompt_version: Mapped[str] = mapped_column(String(120), nullable=False)
    retrieval_configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    environment_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    aggregate_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    failure: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    __table_args__ = (
        UniqueConstraint("evaluation_run_id", "test_case_id", name="uq_eval_result_case"),
        Index("ix_evaluation_results_run_id", "evaluation_run_id"),
        Index("ix_evaluation_results_passed", "passed"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False
    )
    test_case_id: Mapped[str] = mapped_column(String(160), nullable=False)
    question_category: Mapped[str | None] = mapped_column(String(80))
    expected_answerability: Mapped[str | None] = mapped_column(String(40))
    retrieval_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("retrieval_runs.id", ondelete="SET NULL")
    )
    generation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_runs.id", ondelete="SET NULL")
    )
    deterministic_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    judge_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failure_reasons: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
