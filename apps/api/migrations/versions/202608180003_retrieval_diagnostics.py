"""retrieval diagnostics

Revision ID: 202608180003
Revises: 202608180002
Create Date: 2026-08-18 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202608180003"
down_revision: str | None = "202608180002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "retrieval_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("query_text", sa.Text(), nullable=True),
        sa.Column("query_hash", sa.String(length=64), nullable=False),
        sa.Column("query_length", sa.Integer(), nullable=False),
        sa.Column("applied_filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("algorithm_version", sa.String(length=80), nullable=False),
        sa.Column("candidate_counts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reranking_mode", sa.String(length=80), nullable=False),
        sa.Column("degraded_mode", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("latency_ms", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_retrieval_runs_query_hash", "retrieval_runs", ["query_hash"])
    op.create_index("ix_retrieval_runs_created_at", "retrieval_runs", ["created_at"])

    op.create_table(
        "retrieval_run_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("retrieval_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vector_rank", sa.Integer(), nullable=True),
        sa.Column("vector_distance", sa.Float(), nullable=True),
        sa.Column("lexical_rank", sa.Integer(), nullable=True),
        sa.Column("lexical_score", sa.Float(), nullable=True),
        sa.Column("rrf_score", sa.Float(), nullable=True),
        sa.Column("reranker_score", sa.Float(), nullable=True),
        sa.Column("final_rank", sa.Integer(), nullable=True),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("exclusion_reason", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["retrieval_run_id"], ["retrieval_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_retrieval_run_results_run_id", "retrieval_run_results", ["retrieval_run_id"]
    )
    op.create_index("ix_retrieval_run_results_chunk_id", "retrieval_run_results", ["chunk_id"])
    op.create_index("ix_retrieval_run_results_selected", "retrieval_run_results", ["selected"])


def downgrade() -> None:
    op.drop_index("ix_retrieval_run_results_selected", table_name="retrieval_run_results")
    op.drop_index("ix_retrieval_run_results_chunk_id", table_name="retrieval_run_results")
    op.drop_index("ix_retrieval_run_results_run_id", table_name="retrieval_run_results")
    op.drop_table("retrieval_run_results")
    op.drop_index("ix_retrieval_runs_created_at", table_name="retrieval_runs")
    op.drop_index("ix_retrieval_runs_query_hash", table_name="retrieval_runs")
    op.drop_table("retrieval_runs")
