from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, select

from app.core.auth import AdminPrincipal
from app.db.session import async_session_factory
from app.models.discord import DiscordEscalation, DiscordGuildConfig
from app.schemas.discord import (
    DiscordEscalationResponse,
    DiscordEscalationUpdate,
    DiscordGuildConfigResponse,
    DiscordGuildConfigUpdate,
)
from app.services.discord.repository import DiscordRepository

router = APIRouter(prefix="/discord", tags=["discord-admin"])


@router.get("/guilds/{guild_id}", response_model=DiscordGuildConfigResponse)
async def get_guild_config(guild_id: str, _principal: AdminPrincipal) -> DiscordGuildConfigResponse:
    async with async_session_factory() as session:
        config = await DiscordRepository(session).ensure_guild_config(guild_id)
        await session.commit()
        await session.refresh(config)
        return DiscordGuildConfigResponse.model_validate(config, from_attributes=True)


@router.patch("/guilds/{guild_id}", response_model=DiscordGuildConfigResponse)
async def update_guild_config(
    guild_id: str,
    request: DiscordGuildConfigUpdate,
    _principal: AdminPrincipal,
) -> DiscordGuildConfigResponse:
    async with async_session_factory() as session:
        config = await DiscordRepository(session).ensure_guild_config(guild_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(config, field, value)
        await session.commit()
        await session.refresh(config)
        return DiscordGuildConfigResponse.model_validate(config, from_attributes=True)


@router.delete("/guilds/{guild_id}")
async def remove_guild_config(guild_id: str, _principal: AdminPrincipal) -> dict[str, str]:
    async with async_session_factory() as session:
        row = await session.execute(
            select(DiscordGuildConfig).where(DiscordGuildConfig.guild_id == guild_id)
        )
        config = row.scalar_one_or_none()
        if config is None:
            raise HTTPException(status_code=404, detail="Discord guild configuration not found.")
        config.enabled = False
        config.removed_at = datetime.now(UTC)
        await session.commit()
        return {"status": "disabled"}


@router.get("/escalations", response_model=list[DiscordEscalationResponse])
async def list_escalations(
    _principal: AdminPrincipal,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[DiscordEscalationResponse]:
    async with async_session_factory() as session:
        query = select(DiscordEscalation).order_by(desc(DiscordEscalation.created_at))
        if status_filter:
            query = query.where(DiscordEscalation.status == status_filter)
        rows = await session.execute(query.limit(limit))
        return [
            DiscordEscalationResponse.model_validate(row, from_attributes=True)
            for row in rows.scalars()
        ]


@router.patch("/escalations/{escalation_id}", response_model=DiscordEscalationResponse)
async def update_escalation(
    escalation_id: UUID,
    request: DiscordEscalationUpdate,
    _principal: AdminPrincipal,
) -> DiscordEscalationResponse:
    async with async_session_factory() as session:
        escalation = await session.get(DiscordEscalation, escalation_id)
        if escalation is None:
            raise HTTPException(status_code=404, detail="Discord escalation not found.")
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(escalation, field, value)
        await session.commit()
        await session.refresh(escalation)
        return DiscordEscalationResponse.model_validate(escalation, from_attributes=True)
