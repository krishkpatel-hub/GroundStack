from __future__ import annotations

from urllib.parse import urlencode

from app.core.settings import get_settings

DISCORD_SEND_MESSAGES = 1 << 11
DISCORD_EMBED_LINKS = 1 << 14
MINIMAL_BOT_PERMISSIONS = DISCORD_SEND_MESSAGES | DISCORD_EMBED_LINKS


def installation_url(*, application_id: str | None = None) -> str:
    client_id = application_id or get_settings().discord_application_id
    query = urlencode(
        {
            "client_id": client_id,
            "scope": "applications.commands bot",
            "permissions": str(MINIMAL_BOT_PERMISSIONS),
        }
    )
    return f"https://discord.com/oauth2/authorize?{query}"


def command_payloads() -> list[dict[str, object]]:
    return [
        {
            "name": "ask",
            "description": "Ask GroundStack a grounded technical-support question.",
            "options": [
                {
                    "name": "question",
                    "description": "Question to answer from configured GroundStack sources.",
                    "type": 3,
                    "required": True,
                    "max_length": get_settings().discord_max_question_length,
                },
                {
                    "name": "visibility",
                    "description": "Whether the response should be private or public.",
                    "type": 3,
                    "required": False,
                    "choices": [
                        {"name": "private", "value": "private"},
                        {"name": "public", "value": "public"},
                    ],
                },
            ],
        },
        {"name": "help", "description": "Show GroundStack Discord command help."},
        {"name": "status", "description": "Show GroundStack Discord integration status."},
        {"name": "privacy", "description": "Show GroundStack Discord privacy summary."},
        {
            "name": "delete-my-data",
            "description": "Start deletion of stored GroundStack Discord data.",
        },
        {
            "name": "groundstack",
            "description": "Moderator controls for GroundStack Discord integration.",
            "options": [
                {"name": "enable", "description": "Enable GroundStack.", "type": 1},
                {"name": "disable", "description": "Disable GroundStack.", "type": 1},
                {
                    "name": "configure",
                    "description": "Configure server defaults.",
                    "type": 1,
                    "options": [
                        {
                            "name": "default_visibility",
                            "description": "Default answer visibility.",
                            "type": 3,
                            "required": False,
                            "choices": [
                                {"name": "private", "value": "private"},
                                {"name": "public", "value": "public"},
                            ],
                        },
                        {
                            "name": "retention_days",
                            "description": "Discord data retention period.",
                            "type": 4,
                            "required": False,
                            "min_value": 1,
                            "max_value": 365,
                        },
                        {
                            "name": "moderator_channel_id",
                            "description": "Channel ID for human escalations.",
                            "type": 3,
                            "required": False,
                        },
                    ],
                },
                {
                    "name": "channels",
                    "description": "Manage allowed support channels.",
                    "type": 1,
                    "options": [
                        {
                            "name": "action",
                            "description": "Channel action.",
                            "type": 3,
                            "required": False,
                            "choices": [
                                {"name": "list", "value": "list"},
                                {"name": "add", "value": "add"},
                                {"name": "remove", "value": "remove"},
                            ],
                        },
                        {
                            "name": "channel_id",
                            "description": "Discord channel ID.",
                            "type": 3,
                            "required": False,
                        },
                    ],
                },
                {
                    "name": "limits",
                    "description": "Configure Discord rate and capacity limits.",
                    "type": 1,
                    "options": [
                        {
                            "name": "per_user_limit_per_minute",
                            "description": "Per-user question limit.",
                            "type": 4,
                            "required": False,
                            "min_value": 1,
                        },
                        {
                            "name": "per_channel_limit_per_minute",
                            "description": "Per-channel question limit.",
                            "type": 4,
                            "required": False,
                            "min_value": 1,
                        },
                        {
                            "name": "per_guild_limit_per_minute",
                            "description": "Per-server question limit.",
                            "type": 4,
                            "required": False,
                            "min_value": 1,
                        },
                        {
                            "name": "daily_capacity",
                            "description": "Daily server capacity.",
                            "type": 4,
                            "required": False,
                            "min_value": 1,
                        },
                    ],
                },
                {"name": "stats", "description": "Show aggregate GroundStack stats.", "type": 1},
            ],
        },
    ]
