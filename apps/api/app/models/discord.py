import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DiscordGuildConfig(Base):
    __tablename__ = "discord_guild_configs"
    __table_args__ = (
        UniqueConstraint("guild_id", name="uq_discord_guild_configs_guild_id"),
        Index("ix_discord_guild_configs_enabled", "enabled"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_channel_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    moderator_channel_id: Mapped[str | None] = mapped_column(String(32))
    default_visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="private")
    per_user_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    per_channel_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    per_guild_limit_per_minute: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    daily_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    thread_behavior: Mapped[str] = mapped_column(String(24), nullable=False, default="none")
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    enabled_commands: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DiscordInteraction(Base):
    __tablename__ = "discord_interactions"
    __table_args__ = (
        UniqueConstraint("interaction_id", name="uq_discord_interactions_interaction_id"),
        Index("ix_discord_interactions_guild_id", "guild_id"),
        Index("ix_discord_interactions_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id: Mapped[str] = mapped_column(String(32), nullable=False)
    application_id: Mapped[str] = mapped_column(String(32), nullable=False)
    guild_id: Mapped[str | None] = mapped_column(String(32))
    channel_id: Mapped[str | None] = mapped_column(String(32))
    user_hmac: Mapped[str] = mapped_column(String(64), nullable=False)
    command_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_platform: Mapped[str] = mapped_column(String(32), nullable=False, default="discord")
    training_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DiscordJob(Base):
    __tablename__ = "discord_jobs"
    __table_args__ = (
        UniqueConstraint("interaction_id", name="uq_discord_jobs_interaction_id"),
        Index("ix_discord_jobs_status", "status"),
        Index("ix_discord_jobs_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interaction_id: Mapped[str] = mapped_column(String(32), nullable=False)
    application_id: Mapped[str] = mapped_column(String(32), nullable=False)
    guild_id: Mapped[str | None] = mapped_column(String(32))
    channel_id: Mapped[str | None] = mapped_column(String(32))
    user_hmac: Mapped[str] = mapped_column(String(64), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="private")
    encrypted_interaction_token: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    answer_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DiscordFeedback(Base):
    __tablename__ = "discord_feedback"
    __table_args__ = (
        UniqueConstraint("message_id", "user_hmac", name="uq_discord_feedback_message_user"),
        Index("ix_discord_feedback_rating", "rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    guild_id: Mapped[str | None] = mapped_column(String(32))
    channel_id: Mapped[str | None] = mapped_column(String(32))
    user_hmac: Mapped[str] = mapped_column(String(64), nullable=False)
    rating: Mapped[str] = mapped_column(String(16), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(800))
    source_platform: Mapped[str] = mapped_column(String(32), nullable=False, default="discord")
    training_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DiscordControl(Base):
    __tablename__ = "discord_controls"
    __table_args__ = (
        UniqueConstraint("custom_id", name="uq_discord_controls_custom_id"),
        Index("ix_discord_controls_message_id", "message_id"),
        Index("ix_discord_controls_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    custom_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE")
    )
    guild_id: Mapped[str | None] = mapped_column(String(32))
    channel_id: Mapped[str | None] = mapped_column(String(32))
    user_hmac: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DiscordEscalation(Base):
    __tablename__ = "discord_escalations"
    __table_args__ = (
        UniqueConstraint("message_id", "user_hmac", name="uq_discord_escalation_message_user"),
        Index("ix_discord_escalations_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL")
    )
    guild_id: Mapped[str | None] = mapped_column(String(32))
    channel_id: Mapped[str | None] = mapped_column(String(32))
    user_hmac: Mapped[str] = mapped_column(String(64), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_state: Mapped[str] = mapped_column(String(64), nullable=False)
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    assigned_to: Mapped[str | None] = mapped_column(String(120))
    human_response: Mapped[str | None] = mapped_column(Text)
    delivery_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    source_platform: Mapped[str] = mapped_column(String(32), nullable=False, default="discord")
    training_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DiscordDeletionRequest(Base):
    __tablename__ = "discord_deletion_requests"
    __table_args__ = (
        Index("ix_discord_deletion_requests_user_hmac", "user_hmac"),
        Index("ix_discord_deletion_requests_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id: Mapped[str | None] = mapped_column(String(32))
    user_hmac: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_confirmation")
    deleted_counts: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
