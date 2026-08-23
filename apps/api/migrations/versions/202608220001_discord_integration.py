"""discord integration

Revision ID: 202608220001
Revises: 202608200001
Create Date: 2026-08-22
"""

# ruff: noqa: E501

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202608220001"
down_revision: str | None = "202608200001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "message_feedback",
        sa.Column("source_platform", sa.String(length=32), nullable=False, server_default="web"),
    )
    op.add_column(
        "message_feedback",
        sa.Column("training_eligible", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "training_candidates",
        sa.Column("source_platform", sa.String(length=32), nullable=False, server_default="web"),
    )
    op.add_column(
        "training_candidates",
        sa.Column("training_eligible", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_training_candidates_training_eligible", "training_candidates", ["training_eligible"]
    )

    op.create_table(
        "discord_guild_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allowed_channel_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("moderator_channel_id", sa.String(length=32)),
        sa.Column(
            "default_visibility", sa.String(length=16), nullable=False, server_default="private"
        ),
        sa.Column("per_user_limit_per_minute", sa.Integer(), nullable=False, server_default="4"),
        sa.Column(
            "per_channel_limit_per_minute", sa.Integer(), nullable=False, server_default="12"
        ),
        sa.Column("per_guild_limit_per_minute", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("daily_capacity", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("thread_behavior", sa.String(length=24), nullable=False, server_default="none"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("enabled_commands", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("removed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("guild_id", name="uq_discord_guild_configs_guild_id"),
    )
    op.create_index("ix_discord_guild_configs_enabled", "discord_guild_configs", ["enabled"])

    op.create_table(
        "discord_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("interaction_id", sa.String(length=32), nullable=False),
        sa.Column("application_id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32)),
        sa.Column("channel_id", sa.String(length=32)),
        sa.Column("user_hmac", sa.String(length=64), nullable=False),
        sa.Column("command_name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="received"),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column(
            "source_platform", sa.String(length=32), nullable=False, server_default="discord"
        ),
        sa.Column("training_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("interaction_id", name="uq_discord_interactions_interaction_id"),
    )
    op.create_index("ix_discord_interactions_guild_id", "discord_interactions", ["guild_id"])
    op.create_index("ix_discord_interactions_status", "discord_interactions", ["status"])

    op.create_table(
        "discord_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("interaction_id", sa.String(length=32), nullable=False),
        sa.Column("application_id", sa.String(length=32), nullable=False),
        sa.Column("guild_id", sa.String(length=32)),
        sa.Column("channel_id", sa.String(length=32)),
        sa.Column("user_hmac", sa.String(length=64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False, server_default="private"),
        sa.Column("encrypted_interaction_token", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure", postgresql.JSONB()),
        sa.Column("answer_message_id", postgresql.UUID(as_uuid=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("interaction_id", name="uq_discord_jobs_interaction_id"),
    )
    op.create_index("ix_discord_jobs_status", "discord_jobs", ["status"])
    op.create_index("ix_discord_jobs_expires_at", "discord_jobs", ["expires_at"])

    op.create_table(
        "discord_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("guild_id", sa.String(length=32)),
        sa.Column("channel_id", sa.String(length=32)),
        sa.Column("user_hmac", sa.String(length=64), nullable=False),
        sa.Column("rating", sa.String(length=16), nullable=False),
        sa.Column("comment", sa.String(length=800)),
        sa.Column(
            "source_platform", sa.String(length=32), nullable=False, server_default="discord"
        ),
        sa.Column("training_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("message_id", "user_hmac", name="uq_discord_feedback_message_user"),
    )
    op.create_index("ix_discord_feedback_rating", "discord_feedback", ["rating"])

    op.create_table(
        "discord_controls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("custom_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
        ),
        sa.Column("guild_id", sa.String(length=32)),
        sa.Column("channel_id", sa.String(length=32)),
        sa.Column("user_hmac", sa.String(length=64)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("custom_id", name="uq_discord_controls_custom_id"),
    )
    op.create_index("ix_discord_controls_message_id", "discord_controls", ["message_id"])
    op.create_index("ix_discord_controls_expires_at", "discord_controls", ["expires_at"])

    op.create_table(
        "discord_escalations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
        ),
        sa.Column("guild_id", sa.String(length=32)),
        sa.Column("channel_id", sa.String(length=32)),
        sa.Column("user_hmac", sa.String(length=64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_state", sa.String(length=64), nullable=False),
        sa.Column("citations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.String(length=120)),
        sa.Column("human_response", sa.Text()),
        sa.Column(
            "delivery_status", sa.String(length=32), nullable=False, server_default="pending"
        ),
        sa.Column(
            "source_platform", sa.String(length=32), nullable=False, server_default="discord"
        ),
        sa.Column("training_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("message_id", "user_hmac", name="uq_discord_escalation_message_user"),
    )
    op.create_index("ix_discord_escalations_status", "discord_escalations", ["status"])

    op.create_table(
        "discord_deletion_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("guild_id", sa.String(length=32)),
        sa.Column("user_hmac", sa.String(length=64), nullable=False),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="pending_confirmation"
        ),
        sa.Column("deleted_counts", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_discord_deletion_requests_user_hmac", "discord_deletion_requests", ["user_hmac"]
    )
    op.create_index("ix_discord_deletion_requests_status", "discord_deletion_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_discord_deletion_requests_status", table_name="discord_deletion_requests")
    op.drop_index("ix_discord_deletion_requests_user_hmac", table_name="discord_deletion_requests")
    op.drop_table("discord_deletion_requests")
    op.drop_index("ix_discord_escalations_status", table_name="discord_escalations")
    op.drop_table("discord_escalations")
    op.drop_index("ix_discord_feedback_rating", table_name="discord_feedback")
    op.drop_index("ix_discord_controls_expires_at", table_name="discord_controls")
    op.drop_index("ix_discord_controls_message_id", table_name="discord_controls")
    op.drop_table("discord_controls")
    op.drop_table("discord_feedback")
    op.drop_index("ix_discord_jobs_expires_at", table_name="discord_jobs")
    op.drop_index("ix_discord_jobs_status", table_name="discord_jobs")
    op.drop_table("discord_jobs")
    op.drop_index("ix_discord_interactions_status", table_name="discord_interactions")
    op.drop_index("ix_discord_interactions_guild_id", table_name="discord_interactions")
    op.drop_table("discord_interactions")
    op.drop_index("ix_discord_guild_configs_enabled", table_name="discord_guild_configs")
    op.drop_table("discord_guild_configs")
    op.drop_index("ix_training_candidates_training_eligible", table_name="training_candidates")
    op.drop_column("training_candidates", "training_eligible")
    op.drop_column("training_candidates", "source_platform")
    op.drop_column("message_feedback", "training_eligible")
    op.drop_column("message_feedback", "source_platform")
