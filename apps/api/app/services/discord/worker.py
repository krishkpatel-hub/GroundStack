from __future__ import annotations

from uuid import UUID

import httpx

from app.core.settings import get_settings
from app.db.session import async_session_factory
from app.services.ai.types import RetrievalFilters
from app.services.discord.renderer import render_answer
from app.services.discord.repository import DiscordRepository
from app.services.discord.security import decrypt_token
from app.services.generation.service import GroundedAnswerService
from app.services.operations.metrics import metrics


class DiscordDeliveryError(RuntimeError):
    def __init__(self, category: str, *, permanent: bool = False) -> None:
        super().__init__(category)
        self.category = category
        self.permanent = permanent


async def deliver_followup(
    *,
    application_id: str,
    interaction_token: str,
    payload: dict[str, object],
) -> None:
    settings = get_settings()
    url = (
        f"{settings.discord_response_base_url.rstrip('/')}/webhooks/"
        f"{application_id}/{interaction_token}/messages/@original"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.patch(url, json=payload)
    if response.status_code in {401, 403, 404}:
        raise DiscordDeliveryError("discord_authorization_failed", permanent=True)
    if response.status_code == 429:
        raise DiscordDeliveryError("discord_rate_limited")
    if response.status_code >= 500:
        raise DiscordDeliveryError("discord_server_error")
    response.raise_for_status()


async def process_discord_jobs_once() -> int:
    settings = get_settings()
    processed = 0
    async with async_session_factory() as session:
        repo = DiscordRepository(session)
        jobs = await repo.queued_jobs(limit=settings.discord_worker_batch_size)
        for job in jobs:
            processed += 1
            job.status = "processing"
            job.attempts += 1
            await session.commit()
            try:
                result = await GroundedAnswerService().answer(
                    question=job.question,
                    conversation_id=None,
                    client_request_id=job.correlation_id,
                    filters=RetrievalFilters(),
                    owner_subject=f"discord:{job.user_hmac}",
                )
                message_id = result.get("message_id")
                controls = {}
                if message_id:
                    controls = await repo.create_controls(
                        message_id=UUID(str(message_id)),
                        guild_id=job.guild_id,
                        channel_id=job.channel_id,
                        user_hmac=job.user_hmac,
                    )
                rendered = render_answer(
                    answer=str(result.get("answer") or ""),
                    citations=list(result.get("citations") or []),
                    grounding_status=str(result.get("grounding_status") or "unknown"),
                    request_id=job.correlation_id,
                    full_answer_url=None,
                    control_ids=controls,
                )
                payload = {
                    "content": rendered.content,
                    "embeds": rendered.embeds,
                    "components": rendered.components,
                    "allowed_mentions": rendered.allowed_mentions,
                }
                await deliver_followup(
                    application_id=job.application_id,
                    interaction_token=decrypt_token(job.encrypted_interaction_token),
                    payload=payload,
                )
                await repo.mark_job_delivered(
                    job, message_id=UUID(str(message_id)) if message_id else None
                )
                metrics.increment("groundstack_discord_jobs_total", result="delivered")
            except DiscordDeliveryError as exc:
                await repo.mark_job_failed(job, category=exc.category, permanent=exc.permanent)
                metrics.increment(
                    "groundstack_discord_delivery_failures_total", category=exc.category
                )
            except Exception:
                await repo.mark_job_failed(job, category="worker_error", permanent=False)
                metrics.increment("groundstack_discord_jobs_total", result="failed")
            await session.commit()
    return processed
