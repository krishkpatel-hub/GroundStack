from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class DiscordCommandError(ValueError):
    pass


@dataclass(frozen=True)
class AskCommand:
    question: str
    visibility: str


def _options(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") or {}
    values: dict[str, Any] = {}
    for option in data.get("options") or []:
        values[str(option.get("name"))] = option.get("value")
    return values


def _nested_options(option: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for nested in option.get("options") or []:
        values[str(nested.get("name"))] = nested.get("value")
    return values


def command_name(payload: dict[str, Any]) -> str:
    return str((payload.get("data") or {}).get("name") or "")


def groundstack_subcommand(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    options = (payload.get("data") or {}).get("options") or []
    if not options:
        return "stats", {}
    subcommand = options[0]
    return str(subcommand.get("name") or "stats"), _nested_options(subcommand)


def has_moderator_permission(payload: dict[str, Any]) -> bool:
    permissions = str((payload.get("member") or {}).get("permissions") or "0")
    try:
        value = int(permissions)
    except ValueError:
        return False
    manage_guild = 1 << 5
    administrator = 1 << 3
    return bool(value & (manage_guild | administrator))


def parse_ask(payload: dict[str, Any], *, max_length: int) -> AskCommand:
    values = _options(payload)
    question = str(values.get("question") or "").strip()
    if not question:
        raise DiscordCommandError("Question is required.")
    if len(question) > max_length:
        raise DiscordCommandError("Question is too long.")
    visibility = str(values.get("visibility") or "private").strip().lower()
    if visibility not in {"public", "private"}:
        raise DiscordCommandError("Visibility must be public or private.")
    return AskCommand(question=question, visibility=visibility)


def interaction_user_id(payload: dict[str, Any]) -> str:
    member = payload.get("member") or {}
    user = member.get("user") or payload.get("user") or {}
    user_id = str(user.get("id") or "")
    if not user_id:
        raise DiscordCommandError("Discord user ID is missing.")
    return user_id


def component_custom_id(payload: dict[str, Any]) -> str:
    return str((payload.get("data") or {}).get("custom_id") or "")
