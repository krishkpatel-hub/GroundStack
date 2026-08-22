"""grounded generation persistence

Revision ID: 202608190001
Revises: 202608180003
Create Date: 2026-08-19 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202608190001"
down_revision: str | None = "202608180003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("conversations", sa.Column("last_message_at", sa.DateTime(timezone=True)))
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])
    op.create_index("ix_conversations_archived", "conversations", ["archived"])

    op.add_column(
        "messages",
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
    )
    op.add_column("messages", sa.Column("grounding_status", sa.String(length=64)))
    op.add_column("messages", sa.Column("retrieval_run_id", postgresql.UUID(as_uuid=True)))
    op.add_column("messages", sa.Column("generation_run_id", postgresql.UUID(as_uuid=True)))
    op.add_column("messages", sa.Column("provider", sa.String(length=80)))
    op.add_column("messages", sa.Column("model", sa.String(length=200)))
    op.add_column("messages", sa.Column("prompt_version", sa.String(length=120)))
    op.add_column("messages", sa.Column("token_usage", postgresql.JSONB(astext_type=sa.Text())))
    op.add_column("messages", sa.Column("failure", postgresql.JSONB(astext_type=sa.Text())))
    op.add_column("messages", sa.Column("client_request_id", sa.String(length=120)))
    op.add_column("messages", sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.create_foreign_key(
        "fk_messages_retrieval_run_id",
        "messages",
        "retrieval_runs",
        ["retrieval_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_messages_client_request", "messages", ["conversation_id", "client_request_id"]
    )
    op.create_index("ix_messages_generation_run_id", "messages", ["generation_run_id"])
    op.create_index("ix_messages_retrieval_run_id", "messages", ["retrieval_run_id"])
    op.create_index("ix_messages_status", "messages", ["status"])

    op.create_table(
        "generation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True)),
        sa.Column("retrieval_run_id", postgresql.UUID(as_uuid=True)),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("prompt_version", sa.String(length=120), nullable=False),
        sa.Column("prompt_checksum", sa.String(length=64), nullable=False),
        sa.Column("generation_parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("context_citation_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("context_token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "token_counting_mode",
            sa.String(length=40),
            nullable=False,
            server_default="approximate",
        ),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("first_token_latency_ms", sa.Float()),
        sa.Column("total_latency_ms", sa.Float()),
        sa.Column("finish_reason", sa.String(length=80)),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("repair_attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("rendered_prompt", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["retrieval_run_id"], ["retrieval_runs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_generation_runs_conversation_id", "generation_runs", ["conversation_id"])
    op.create_index("ix_generation_runs_message_id", "generation_runs", ["message_id"])
    op.create_index("ix_generation_runs_retrieval_run_id", "generation_runs", ["retrieval_run_id"])
    op.create_index("ix_generation_runs_status", "generation_runs", ["status"])

    op.create_table(
        "message_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("citation_id", sa.String(length=16), nullable=False),
        sa.Column("citation_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("message_id", "citation_id", name="uq_message_citation_id"),
        sa.UniqueConstraint("message_id", "chunk_id", name="uq_message_citation_chunk"),
    )
    op.create_index("ix_message_citations_message_id", "message_citations", ["message_id"])
    op.create_index("ix_message_citations_chunk_id", "message_citations", ["chunk_id"])


def downgrade() -> None:
    op.drop_index("ix_message_citations_chunk_id", table_name="message_citations")
    op.drop_index("ix_message_citations_message_id", table_name="message_citations")
    op.drop_table("message_citations")
    op.drop_index("ix_generation_runs_status", table_name="generation_runs")
    op.drop_index("ix_generation_runs_retrieval_run_id", table_name="generation_runs")
    op.drop_index("ix_generation_runs_message_id", table_name="generation_runs")
    op.drop_index("ix_generation_runs_conversation_id", table_name="generation_runs")
    op.drop_table("generation_runs")
    op.drop_index("ix_messages_status", table_name="messages")
    op.drop_index("ix_messages_retrieval_run_id", table_name="messages")
    op.drop_index("ix_messages_generation_run_id", table_name="messages")
    op.drop_constraint("uq_messages_client_request", "messages", type_="unique")
    op.drop_constraint("fk_messages_retrieval_run_id", "messages", type_="foreignkey")
    for column in [
        "completed_at",
        "client_request_id",
        "failure",
        "token_usage",
        "prompt_version",
        "model",
        "provider",
        "generation_run_id",
        "retrieval_run_id",
        "grounding_status",
        "status",
    ]:
        op.drop_column("messages", column)
    op.drop_index("ix_conversations_archived", table_name="conversations")
    op.drop_index("ix_conversations_last_message_at", table_name="conversations")
    op.drop_column("conversations", "last_message_at")
    op.drop_column("conversations", "archived")
