from __future__ import annotations

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.models.conversation import Message
from app.models.discord import (
    DiscordControl,
    DiscordDeletionRequest,
    DiscordEscalation,
    DiscordFeedback,
    DiscordGuildConfig,
    DiscordInteraction,
    DiscordJob,
)
from app.services.discord.security import encrypt_token

DEFAULT_COMMANDS = [
    "ask",
    "help",
    "status",
    "privacy",
    "delete-my-data",
    "groundstack",
]


class DiscordAuthorizationError(PermissionError):
    pass


class DiscordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def guild_config(self, guild_id: str | None) -> DiscordGuildConfig | None:
        if not guild_id:
            return None
        row = await self.session.execute(
            select(DiscordGuildConfig).where(DiscordGuildConfig.guild_id == guild_id)
        )
        return row.scalar_one_or_none()

    async def ensure_guild_config(self, guild_id: str) -> DiscordGuildConfig:
        config = await self.guild_config(guild_id)
        if config:
            return config
        settings = get_settings()
        config = DiscordGuildConfig(
            guild_id=guild_id,
            enabled=False,
            default_visibility="private",
            retention_days=settings.discord_default_retention_days,
            enabled_commands=DEFAULT_COMMANDS,
        )
        self.session.add(config)
        await self.session.flush()
        return config

    async def authorize(
        self, *, guild_id: str | None, channel_id: str | None
    ) -> DiscordGuildConfig:
        settings = get_settings()
        if guild_id is None and not settings.discord_allow_dms:
            raise DiscordAuthorizationError("GroundStack is not enabled in direct messages.")
        config = await self.guild_config(guild_id)
        if config is None or not config.enabled:
            raise DiscordAuthorizationError("GroundStack is not enabled for this server.")
        if config.allowed_channel_ids and channel_id not in config.allowed_channel_ids:
            raise DiscordAuthorizationError("GroundStack is not enabled in this channel.")
        return config

    async def interaction_seen(self, interaction_id: str) -> bool:
        row = await self.session.execute(
            select(DiscordInteraction.id).where(DiscordInteraction.interaction_id == interaction_id)
        )
        return row.scalar_one_or_none() is not None

    async def record_interaction(
        self,
        *,
        interaction_id: str,
        application_id: str,
        guild_id: str | None,
        channel_id: str | None,
        user_hmac: str,
        command_name: str,
        correlation_id: str,
        status: str = "received",
    ) -> DiscordInteraction:
        interaction = DiscordInteraction(
            interaction_id=interaction_id,
            application_id=application_id,
            guild_id=guild_id,
            channel_id=channel_id,
            user_hmac=user_hmac,
            command_name=command_name,
            correlation_id=correlation_id,
            status=status,
            training_eligible=False,
        )
        self.session.add(interaction)
        await self.session.flush()
        return interaction

    async def create_job(
        self,
        *,
        interaction_id: str,
        application_id: str,
        guild_id: str | None,
        channel_id: str | None,
        user_hmac: str,
        question: str,
        visibility: str,
        interaction_token: str,
        correlation_id: str,
    ) -> DiscordJob:
        existing = await self.session.execute(
            select(DiscordJob).where(DiscordJob.interaction_id == interaction_id)
        )
        job = existing.scalar_one_or_none()
        if job:
            return job
        expires_at = datetime.now(UTC) + timedelta(seconds=get_settings().discord_queue_ttl_seconds)
        job = DiscordJob(
            interaction_id=interaction_id,
            application_id=application_id,
            guild_id=guild_id,
            channel_id=channel_id,
            user_hmac=user_hmac,
            question=question,
            visibility=visibility,
            encrypted_interaction_token=encrypt_token(interaction_token),
            correlation_id=correlation_id,
            expires_at=expires_at,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def queued_jobs(self, *, limit: int) -> list[DiscordJob]:
        row = await self.session.execute(
            select(DiscordJob)
            .where(DiscordJob.status.in_(["queued", "retry"]))
            .where(DiscordJob.expires_at > datetime.now(UTC))
            .order_by(DiscordJob.created_at)
            .limit(limit)
        )
        return list(row.scalars())

    async def mark_job_failed(self, job: DiscordJob, *, category: str, permanent: bool) -> None:
        job.status = (
            "failed"
            if permanent or job.attempts > get_settings().discord_worker_max_retries
            else "retry"
        )
        job.failure = {"category": category, "permanent": permanent}
        await self.session.flush()

    async def mark_job_delivered(self, job: DiscordJob, *, message_id: UUID | None) -> None:
        job.status = "delivered"
        job.delivered_at = datetime.now(UTC)
        job.answer_message_id = message_id
        job.encrypted_interaction_token = ""
        await self.session.flush()

    async def upsert_feedback(
        self,
        *,
        message_id: UUID,
        guild_id: str | None,
        channel_id: str | None,
        user_hmac: str,
        rating: str,
        comment: str | None = None,
    ) -> DiscordFeedback:
        row = await self.session.execute(
            select(DiscordFeedback).where(
                DiscordFeedback.message_id == message_id,
                DiscordFeedback.user_hmac == user_hmac,
            )
        )
        feedback = row.scalar_one_or_none()
        if feedback is None:
            feedback = DiscordFeedback(
                message_id=message_id,
                guild_id=guild_id,
                channel_id=channel_id,
                user_hmac=user_hmac,
            )
            self.session.add(feedback)
        feedback.rating = rating
        feedback.comment = comment
        feedback.training_eligible = False
        await self.session.flush()
        return feedback

    async def create_controls(
        self,
        *,
        message_id: UUID,
        guild_id: str | None,
        channel_id: str | None,
        user_hmac: str,
    ) -> dict[str, str]:
        expires_at = datetime.now(UTC) + timedelta(
            days=get_settings().discord_default_retention_days
        )
        result: dict[str, str] = {}
        for action in ["helpful", "not_helpful", "sources", "escalate"]:
            custom_id = f"gs:{token_urlsafe(18)}"
            self.session.add(
                DiscordControl(
                    custom_id=custom_id,
                    action=action,
                    message_id=message_id,
                    guild_id=guild_id,
                    channel_id=channel_id,
                    user_hmac=user_hmac,
                    expires_at=expires_at,
                )
            )
            result[action] = custom_id
        await self.session.flush()
        return result

    async def create_delete_control(self, *, guild_id: str | None, user_hmac: str) -> str:
        custom_id = f"gs:{token_urlsafe(18)}"
        self.session.add(
            DiscordControl(
                custom_id=custom_id,
                action="delete_confirm",
                message_id=None,
                guild_id=guild_id,
                channel_id=None,
                user_hmac=user_hmac,
                expires_at=datetime.now(UTC) + timedelta(minutes=10),
            )
        )
        await self.session.flush()
        return custom_id

    async def guild_stats(self, *, guild_id: str | None) -> dict[str, int]:
        if not guild_id:
            return {"queued_jobs": 0, "open_escalations": 0, "feedback": 0}
        queued_jobs = await self.session.scalar(
            select(func.count(DiscordJob.id)).where(
                DiscordJob.guild_id == guild_id,
                DiscordJob.status.in_(["queued", "retry", "processing"]),
            )
        )
        open_escalations = await self.session.scalar(
            select(func.count(DiscordEscalation.id)).where(
                DiscordEscalation.guild_id == guild_id,
                DiscordEscalation.status.in_(["open", "assigned"]),
            )
        )
        feedback = await self.session.scalar(
            select(func.count(DiscordFeedback.id)).where(DiscordFeedback.guild_id == guild_id)
        )
        return {
            "queued_jobs": int(queued_jobs or 0),
            "open_escalations": int(open_escalations or 0),
            "feedback": int(feedback or 0),
        }

    async def get_control(self, custom_id: str) -> DiscordControl | None:
        row = await self.session.execute(
            select(DiscordControl).where(
                DiscordControl.custom_id == custom_id,
                DiscordControl.expires_at > datetime.now(UTC),
            )
        )
        return row.scalar_one_or_none()

    async def create_escalation(
        self,
        *,
        message_id: UUID | None,
        guild_id: str | None,
        channel_id: str | None,
        user_hmac: str,
        question: str,
        answer_state: str,
        citations: list[dict[str, Any]],
        request_id: str,
    ) -> DiscordEscalation:
        query = select(DiscordEscalation).where(DiscordEscalation.user_hmac == user_hmac)
        if message_id:
            query = query.where(DiscordEscalation.message_id == message_id)
        row = await self.session.execute(query)
        existing = row.scalar_one_or_none()
        if existing:
            return existing
        escalation = DiscordEscalation(
            message_id=message_id,
            guild_id=guild_id,
            channel_id=channel_id,
            user_hmac=user_hmac,
            question=question,
            answer_state=answer_state,
            citations=citations,
            request_id=request_id,
            training_eligible=False,
        )
        self.session.add(escalation)
        await self.session.flush()
        return escalation

    async def request_deletion(
        self, *, guild_id: str | None, user_hmac: str
    ) -> DiscordDeletionRequest:
        request = DiscordDeletionRequest(guild_id=guild_id, user_hmac=user_hmac)
        self.session.add(request)
        await self.session.flush()
        return request

    async def delete_user_data(self, *, guild_id: str | None, user_hmac: str) -> dict[str, int]:
        async def delete_and_count(model: type, *filters: Any) -> int:
            rows = await self.session.execute(select(model.id).where(*filters))
            ids = list(rows.scalars())
            if ids:
                await self.session.execute(delete(model).where(model.id.in_(ids)))
            return len(ids)

        filters = [DiscordFeedback.user_hmac == user_hmac]
        if guild_id:
            filters.append(DiscordFeedback.guild_id == guild_id)
        feedback_count = await delete_and_count(DiscordFeedback, *filters)

        escalation_filters = [DiscordEscalation.user_hmac == user_hmac]
        if guild_id:
            escalation_filters.append(DiscordEscalation.guild_id == guild_id)
        escalation_count = await delete_and_count(DiscordEscalation, *escalation_filters)

        interaction_filters = [DiscordInteraction.user_hmac == user_hmac]
        if guild_id:
            interaction_filters.append(DiscordInteraction.guild_id == guild_id)
        interaction_count = await delete_and_count(DiscordInteraction, *interaction_filters)

        job_filters = [DiscordJob.user_hmac == user_hmac]
        if guild_id:
            job_filters.append(DiscordJob.guild_id == guild_id)
        job_count = await delete_and_count(DiscordJob, *job_filters)

        message_count = await delete_and_count(
            Message,
            Message.owner_subject == f"discord:{user_hmac}",
        )
        return {
            "feedback": feedback_count,
            "escalations": escalation_count,
            "interactions": interaction_count,
            "jobs": job_count,
            "messages": message_count,
        }
