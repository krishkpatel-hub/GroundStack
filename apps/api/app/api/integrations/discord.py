from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.settings import get_settings
from app.db.session import async_session_factory
from app.models.discord import DiscordControl
from app.services.discord.commands import (
    DiscordCommandError,
    command_name,
    component_custom_id,
    groundstack_subcommand,
    has_moderator_permission,
    interaction_user_id,
    parse_ask,
)
from app.services.discord.renderer import deferred_message, simple_message
from app.services.discord.replay import claim_interaction
from app.services.discord.repository import DiscordAuthorizationError, DiscordRepository
from app.services.discord.security import DiscordSecurityError, user_hmac, verify_signature
from app.services.operations.demo_limits import demo_availability
from app.services.operations.metrics import metrics
from app.services.operations.rate_limit import limiter

router = APIRouter(prefix="/integrations/discord", tags=["discord"])


def _json(payload: dict) -> JSONResponse:
    return JSONResponse(payload, headers={"X-Content-Type-Options": "nosniff"})


def _ids(payload: dict) -> tuple[str | None, str | None]:
    return payload.get("guild_id"), payload.get("channel_id")


async def _verify(request: Request, body: bytes) -> None:
    try:
        verify_signature(
            body=body,
            timestamp=request.headers.get("x-signature-timestamp", ""),
            signature=request.headers.get("x-signature-ed25519", ""),
        )
    except DiscordSecurityError as exc:
        metrics.increment("groundstack_discord_interactions_total", result="invalid_signature")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/interactions")
async def discord_interactions(request: Request) -> JSONResponse:
    settings = get_settings()
    body = await request.body()
    await _verify(request, body)
    payload = await request.json()
    interaction_type = int(payload.get("type") or 0)
    if interaction_type == 1:
        return _json({"type": 1})
    if not settings.discord_integration_enabled:
        return _json(simple_message("GroundStack Discord integration is not enabled."))

    if interaction_type == 2:
        return await _application_command(payload)
    if interaction_type == 3:
        return await _component(payload)
    if interaction_type == 5:
        return _json(simple_message("GroundStack received a modal submission."))
    return _json(simple_message("Unsupported GroundStack Discord interaction."))


async def _application_command(payload: dict) -> JSONResponse:
    settings = get_settings()
    name = command_name(payload)
    interaction_id = str(payload.get("id") or "")
    application_id = str(payload.get("application_id") or settings.discord_application_id)
    token = str(payload.get("token") or "")
    guild_id, channel_id = _ids(payload)
    correlation_id = str(uuid4())
    try:
        hmac_user = user_hmac(interaction_user_id(payload))
    except (DiscordSecurityError, DiscordCommandError) as exc:
        return _json(simple_message(str(exc)))

    async with async_session_factory() as session:
        repo = DiscordRepository(session)
        replay_claimed = await claim_interaction(interaction_id)
        if replay_claimed is False or (
            replay_claimed is None and await repo.interaction_seen(interaction_id)
        ):
            metrics.increment("groundstack_discord_interactions_total", result="duplicate")
            return _json(deferred_message(ephemeral=True))
        await repo.record_interaction(
            interaction_id=interaction_id,
            application_id=application_id,
            guild_id=guild_id,
            channel_id=channel_id,
            user_hmac=hmac_user,
            command_name=name,
            correlation_id=correlation_id,
        )
        try:
            if name == "ask":
                config = await repo.authorize(guild_id=guild_id, channel_id=channel_id)
                availability = await demo_availability()
                if not availability.chat_enabled:
                    await session.commit()
                    return _json(simple_message("GroundStack is temporarily unavailable."))
                ask = parse_ask(payload, max_length=settings.discord_max_question_length)
                visibility = ask.visibility or config.default_visibility
                user_decision = await limiter(
                    "discord-user", limit=config.per_user_limit_per_minute
                ).check(f"discord:user:{hmac_user}")
                channel_decision = await limiter(
                    "discord-channel", limit=config.per_channel_limit_per_minute
                ).check(f"discord:channel:{guild_id}:{channel_id}")
                guild_decision = await limiter(
                    "discord-guild", limit=config.per_guild_limit_per_minute
                ).check(f"discord:guild:{guild_id}")
                if not (
                    user_decision.allowed and channel_decision.allowed and guild_decision.allowed
                ):
                    await session.commit()
                    metrics.increment(
                        "groundstack_discord_interactions_total", result="rate_limited"
                    )
                    return _json(simple_message("GroundStack Discord rate limit reached."))
                await repo.create_job(
                    interaction_id=interaction_id,
                    application_id=application_id,
                    guild_id=guild_id,
                    channel_id=channel_id,
                    user_hmac=hmac_user,
                    question=ask.question,
                    visibility=visibility,
                    interaction_token=token,
                    correlation_id=correlation_id,
                )
                await session.commit()
                metrics.increment("groundstack_discord_interactions_total", result="accepted")
                return _json(deferred_message(ephemeral=visibility == "private"))
            if name == "help":
                await session.commit()
                return _json(
                    simple_message(
                        "Use `/ask question:<text> visibility:<public|private>`. "
                        "GroundStack only processes explicit slash-command questions."
                    )
                )
            if name == "status":
                config = await repo.guild_config(guild_id)
                state = "enabled" if config and config.enabled else "disabled"
                await session.commit()
                return _json(simple_message(f"GroundStack Discord integration is {state}."))
            if name == "privacy":
                await session.commit()
                return _json(
                    simple_message(
                        "GroundStack stores only the explicit command question, a keyed user "
                        "identifier, delivery state, feedback, and escalation records. It does "
                        "not scan normal messages or use Discord data for training."
                    )
                )
            if name == "delete-my-data":
                custom_id = await repo.create_delete_control(guild_id=guild_id, user_hmac=hmac_user)
                await repo.request_deletion(guild_id=guild_id, user_hmac=hmac_user)
                await session.commit()
                return _json(
                    {
                        "type": 4,
                        "data": {
                            "content": "Confirm deletion of stored GroundStack Discord data?",
                            "flags": 64,
                            "allowed_mentions": {"parse": []},
                            "components": [
                                {
                                    "type": 1,
                                    "components": [
                                        {
                                            "type": 2,
                                            "style": 4,
                                            "label": "Confirm deletion",
                                            "custom_id": custom_id,
                                        }
                                    ],
                                }
                            ],
                        },
                    }
                )
            if name == "groundstack":
                message = await _handle_groundstack_command(repo, payload, guild_id)
                await session.commit()
                return _json(simple_message(message))
        except DiscordAuthorizationError as exc:
            await session.commit()
            return _json(simple_message(str(exc)))
        except DiscordCommandError as exc:
            await session.commit()
            return _json(simple_message(str(exc)))
    return _json(simple_message("Unknown GroundStack command."))


async def _handle_groundstack_command(
    repo: DiscordRepository, payload: dict, guild_id: str | None
) -> str:
    if not guild_id:
        raise DiscordAuthorizationError("GroundStack server configuration is not available in DMs.")
    if not has_moderator_permission(payload):
        raise DiscordAuthorizationError("A server moderator must run GroundStack configuration.")
    subcommand, options = groundstack_subcommand(payload)
    config = await repo.ensure_guild_config(guild_id)
    if subcommand == "enable":
        config.enabled = True
        return "GroundStack is enabled for this server."
    if subcommand == "disable":
        config.enabled = False
        return "GroundStack is disabled for this server."
    if subcommand == "configure":
        if "default_visibility" in options:
            visibility = str(options["default_visibility"]).lower()
            if visibility not in {"public", "private"}:
                raise DiscordCommandError("Default visibility must be public or private.")
            config.default_visibility = visibility
        if "retention_days" in options:
            config.retention_days = max(1, min(365, int(options["retention_days"])))
        if "moderator_channel_id" in options:
            config.moderator_channel_id = str(options["moderator_channel_id"])
        return "GroundStack server defaults were updated."
    if subcommand == "channels":
        action = str(options.get("action") or "list").lower()
        channel_id = str(options.get("channel_id") or "").strip()
        channels = list(config.allowed_channel_ids or [])
        if action == "add" and channel_id:
            if channel_id not in channels:
                channels.append(channel_id)
            config.allowed_channel_ids = channels
            return f"Allowed channel added. Total configured channels: {len(channels)}."
        if action == "remove" and channel_id:
            config.allowed_channel_ids = [item for item in channels if item != channel_id]
            count = len(config.allowed_channel_ids)
            return f"Allowed channel removed. Total configured channels: {count}."
        return f"Allowed channels configured: {len(channels)}."
    if subcommand == "limits":
        for field in [
            "per_user_limit_per_minute",
            "per_channel_limit_per_minute",
            "per_guild_limit_per_minute",
            "daily_capacity",
        ]:
            if field in options:
                setattr(config, field, max(1, int(options[field])))
        return "GroundStack rate and capacity limits were updated."
    if subcommand == "stats":
        stats = await repo.guild_stats(guild_id=guild_id)
        return (
            "GroundStack Discord stats: "
            f"{stats['queued_jobs']} queued jobs, "
            f"{stats['open_escalations']} open escalations, "
            f"{stats['feedback']} feedback records."
        )
    raise DiscordCommandError("Unknown GroundStack moderator command.")


async def _component(payload: dict) -> JSONResponse:
    custom_id = component_custom_id(payload)
    guild_id, channel_id = _ids(payload)
    try:
        hmac_user = user_hmac(interaction_user_id(payload))
    except (DiscordSecurityError, DiscordCommandError) as exc:
        return _json(simple_message(str(exc)))
    async with async_session_factory() as session:
        repo = DiscordRepository(session)
        control = await repo.get_control(custom_id)
        if control is None:
            return _json(simple_message("This GroundStack control expired."))
        if control.user_hmac and control.user_hmac != hmac_user:
            return _json(simple_message("This control belongs to another user."))
        if control.guild_id and control.guild_id != guild_id:
            return _json(simple_message("This control is not valid for this server."))
        if control.channel_id and control.channel_id != channel_id:
            return _json(simple_message("This control is not valid for this channel."))
        response = await _handle_control(repo, control, guild_id, channel_id, hmac_user)
        control.used_at = datetime.now(UTC)
        await session.commit()
        return _json(response)


async def _handle_control(
    repo: DiscordRepository,
    control: DiscordControl,
    guild_id: str | None,
    channel_id: str | None,
    hmac_user: str,
) -> dict:
    if control.action in {"helpful", "not_helpful"} and control.message_id:
        await repo.upsert_feedback(
            message_id=control.message_id,
            guild_id=guild_id,
            channel_id=channel_id,
            user_hmac=hmac_user,
            rating="positive" if control.action == "helpful" else "negative",
        )
        return simple_message(
            "Feedback saved. You can change it by pressing another feedback button."
        )
    if control.action == "sources":
        return simple_message(
            "Sources are shown in the answer citations. Full source viewer support is "
            "available in the web app."
        )
    if control.action == "escalate":
        await repo.create_escalation(
            message_id=control.message_id,
            guild_id=guild_id,
            channel_id=channel_id,
            user_hmac=hmac_user,
            question="Stored GroundStack Discord question",
            answer_state="user_requested_human",
            citations=[],
            request_id=str(uuid4()),
        )
        return simple_message("A human escalation was recorded for moderators.")
    if control.action == "delete_confirm":
        counts = await repo.delete_user_data(guild_id=guild_id, user_hmac=hmac_user)
        return simple_message(f"Deletion completed. Removed records: {counts}.")
    return simple_message("Unsupported GroundStack control.")
