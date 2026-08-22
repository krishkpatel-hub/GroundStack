"""feedback, training candidates, and evaluation persistence

Revision ID: 202608190002
Revises: 202608190001
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202608190002"
down_revision: str | None = "202608190001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "message_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.String(length=16), nullable=False),
        sa.Column("categories", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("comment", sa.String(length=1000)),
        sa.Column("suggested_correction", sa.String(length=3000)),
        sa.Column("citations_incorrect", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reported_citation_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("client_request_id", sa.String(length=120), nullable=False),
        sa.Column("message_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "message_id", "client_request_id", name="uq_message_feedback_message_client"
        ),
    )
    op.create_index("ix_message_feedback_conversation_id", "message_feedback", ["conversation_id"])
    op.create_index("ix_message_feedback_rating", "message_feedback", ["rating"])

    op.create_table(
        "training_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feedback_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("proposed_question", sa.Text(), nullable=False),
        sa.Column("evidence_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("proposed_answer", sa.Text(), nullable=False),
        sa.Column("citation_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "redaction_status", sa.String(length=32), nullable=False, server_default="pending"
        ),
        sa.Column(
            "provenance_status", sa.String(length=32), nullable=False, server_default="pending"
        ),
        sa.Column("reviewer_notes", sa.String(length=2000)),
        sa.Column("reviewer_identifier", sa.String(length=120)),
        sa.Column(
            "dataset_export_status",
            sa.String(length=32),
            nullable=False,
            server_default="not_exported",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feedback_id"], ["message_feedback.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "message_id", "feedback_id", name="uq_training_candidate_message_feedback"
        ),
    )
    op.create_index("ix_training_candidates_status", "training_candidates", ["status"])
    op.create_index("ix_training_candidates_message_id", "training_candidates", ["message_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("suite_names", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dataset_version", sa.String(length=120), nullable=False),
        sa.Column("dataset_checksum", sa.String(length=64), nullable=False),
        sa.Column("model_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prompt_version", sa.String(length=120), nullable=False),
        sa.Column(
            "retrieval_configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("environment_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("aggregate_metrics", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("failure", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_evaluation_runs_status", "evaluation_runs", ["status"])
    op.create_index("ix_evaluation_runs_created_at", "evaluation_runs", ["created_at"])

    op.create_table(
        "evaluation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_case_id", sa.String(length=160), nullable=False),
        sa.Column("question_category", sa.String(length=80)),
        sa.Column("expected_answerability", sa.String(length=40)),
        sa.Column("retrieval_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("generation_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("deterministic_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("judge_metrics", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("failure_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("latency_ms", sa.Float()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["retrieval_run_id"], ["retrieval_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["generation_run_id"], ["generation_runs.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("evaluation_run_id", "test_case_id", name="uq_eval_result_case"),
    )
    op.create_index("ix_evaluation_results_run_id", "evaluation_results", ["evaluation_run_id"])
    op.create_index("ix_evaluation_results_passed", "evaluation_results", ["passed"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_results_passed", table_name="evaluation_results")
    op.drop_index("ix_evaluation_results_run_id", table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index("ix_evaluation_runs_created_at", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_status", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_index("ix_training_candidates_message_id", table_name="training_candidates")
    op.drop_index("ix_training_candidates_status", table_name="training_candidates")
    op.drop_table("training_candidates")
    op.drop_index("ix_message_feedback_rating", table_name="message_feedback")
    op.drop_index("ix_message_feedback_conversation_id", table_name="message_feedback")
    op.drop_table("message_feedback")
