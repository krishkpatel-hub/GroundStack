import pytest

from app.services.discord.commands import (
    DiscordCommandError,
    groundstack_subcommand,
    has_moderator_permission,
    parse_ask,
)
from app.services.discord.registration import (
    MINIMAL_BOT_PERMISSIONS,
    command_payloads,
    installation_url,
)
from app.services.discord.renderer import render_answer, sanitize_markdown, suppress_mentions


def test_parse_ask_requires_explicit_question() -> None:
    payload = {"data": {"options": [{"name": "visibility", "value": "private"}]}}

    with pytest.raises(DiscordCommandError):
        parse_ask(payload, max_length=100)


def test_parse_ask_validates_visibility() -> None:
    payload = {
        "data": {
            "options": [
                {"name": "question", "value": "How do I configure GroundStack?"},
                {"name": "visibility", "value": "public"},
            ]
        }
    }

    command = parse_ask(payload, max_length=100)

    assert command.question == "How do I configure GroundStack?"
    assert command.visibility == "public"


def test_mentions_are_suppressed() -> None:
    assert "@\u200beveryone" in suppress_mentions("@everyone check this")
    assert "<@\u200b123>" in suppress_mentions("<@123>")


def test_markdown_link_spoofing_is_sanitized() -> None:
    assert sanitize_markdown("[click](javascript:alert(1))") == "click"


def test_renderer_uses_opaque_component_ids() -> None:
    rendered = render_answer(
        answer="Use the setup guide [C1].",
        citations=[{"document_title": "Setup", "section": "Install"}],
        grounding_status="fully_grounded",
        request_id="req-1",
        full_answer_url=None,
        control_ids={
            "helpful": "gs:opaque1",
            "not_helpful": "gs:opaque2",
            "sources": "gs:opaque3",
            "escalate": "gs:opaque4",
        },
    )

    custom_ids = [item["custom_id"] for item in rendered.components[0]["components"]]
    assert custom_ids == ["gs:opaque1", "gs:opaque2", "gs:opaque3", "gs:opaque4"]
    assert rendered.allowed_mentions == {"parse": []}


def test_groundstack_subcommand_parses_nested_options() -> None:
    payload = {
        "data": {
            "name": "groundstack",
            "options": [
                {
                    "name": "channels",
                    "options": [
                        {"name": "action", "value": "add"},
                        {"name": "channel_id", "value": "123"},
                    ],
                }
            ],
        }
    }

    name, options = groundstack_subcommand(payload)

    assert name == "channels"
    assert options == {"action": "add", "channel_id": "123"}


def test_moderator_permission_accepts_manage_guild_without_bot_admin() -> None:
    assert has_moderator_permission({"member": {"permissions": str(1 << 5)}})
    assert not has_moderator_permission({"member": {"permissions": "0"}})


def test_command_payloads_use_explicit_slash_commands() -> None:
    names = {command["name"] for command in command_payloads()}

    assert {"ask", "help", "status", "privacy", "delete-my-data", "groundstack"} <= names
    assert installation_url(application_id="app-id").startswith(
        "https://discord.com/oauth2/authorize?"
    )
    assert MINIMAL_BOT_PERMISSIONS & (1 << 3) == 0
