from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DiscordGuildConfigResponse(BaseModel):
    id: UUID
    guild_id: str
    enabled: bool
    allowed_channel_ids: list[str]
    moderator_channel_id: str | None
    default_visibility: str
    per_user_limit_per_minute: int
    per_channel_limit_per_minute: int
    per_guild_limit_per_minute: int
    daily_capacity: int
    thread_behavior: str
    retention_days: int
    enabled_commands: list[str]
    created_at: datetime
    updated_at: datetime


class DiscordGuildConfigUpdate(BaseModel):
    enabled: bool | None = None
    allowed_channel_ids: list[str] | None = None
    moderator_channel_id: str | None = None
    default_visibility: str | None = Field(default=None, pattern="^(public|private)$")
    per_user_limit_per_minute: int | None = Field(default=None, ge=1, le=60)
    per_channel_limit_per_minute: int | None = Field(default=None, ge=1, le=300)
    per_guild_limit_per_minute: int | None = Field(default=None, ge=1, le=1000)
    daily_capacity: int | None = Field(default=None, ge=1, le=10000)
    thread_behavior: str | None = Field(default=None, pattern="^(none|thread)$")
    retention_days: int | None = Field(default=None, ge=1, le=365)
    enabled_commands: list[str] | None = None


class DiscordEscalationResponse(BaseModel):
    id: UUID
    message_id: UUID | None
    guild_id: str | None
    channel_id: str | None
    question: str
    answer_state: str
    citations: list[dict[str, object]]
    request_id: str
    status: str
    assigned_to: str | None
    human_response: str | None
    delivery_status: str
    created_at: datetime
    updated_at: datetime


class DiscordEscalationUpdate(BaseModel):
    status: str | None = Field(
        default=None, pattern="^(open|assigned|resolved|duplicate|out_of_scope)$"
    )
    assigned_to: str | None = Field(default=None, max_length=120)
    human_response: str | None = Field(default=None, max_length=3000)
    delivery_status: str | None = Field(default=None, pattern="^(pending|delivered|failed)$")
