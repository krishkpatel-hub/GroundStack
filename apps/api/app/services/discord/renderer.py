from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

DISCORD_CONTENT_LIMIT = 2000
EMBED_DESCRIPTION_LIMIT = 4096
MAX_CITATIONS = 5
ZERO_WIDTH = "\u200b"


@dataclass(frozen=True)
class DiscordRenderedAnswer:
    content: str
    embeds: list[dict[str, Any]]
    components: list[dict[str, Any]]
    allowed_mentions: dict[str, list[str]]


def suppress_mentions(text: str) -> str:
    return (
        text.replace("@everyone", f"@{ZERO_WIDTH}everyone")
        .replace("@here", f"@{ZERO_WIDTH}here")
        .replace("<@", f"<@{ZERO_WIDTH}")
        .replace("<#", f"<#{ZERO_WIDTH}")
        .replace("<@&", f"<@&{ZERO_WIDTH}")
    )


def sanitize_markdown(text: str) -> str:
    text = suppress_mentions(text)
    text = re.sub(r"\[([^\]]{1,120})\]\((?!https?://)(?:[^()]|\([^)]*\))*\)", r"\1", text)
    return text.replace("```", "`\u200b``")


def _citation_line(index: int, citation: dict[str, Any]) -> str:
    title = sanitize_markdown(
        str(citation.get("document_title") or citation.get("title") or "Source")
    )
    section = citation.get("section") or citation.get("heading_path") or citation.get("page")
    if isinstance(section, list):
        section = " > ".join(str(item) for item in section)
    suffix = f" - {sanitize_markdown(str(section))}" if section else ""
    return f"{index}. {title}{suffix}"


def render_answer(
    *,
    answer: str,
    citations: list[dict[str, Any]],
    grounding_status: str,
    request_id: str,
    full_answer_url: str | None,
    control_ids: dict[str, str] | None = None,
) -> DiscordRenderedAnswer:
    safe_answer = sanitize_markdown(answer).strip()
    if len(safe_answer) > EMBED_DESCRIPTION_LIMIT - 800:
        safe_answer = safe_answer[: EMBED_DESCRIPTION_LIMIT - 820].rstrip() + "\n\n[Truncated]"
    citation_lines = [
        _citation_line(index, citation)
        for index, citation in enumerate(citations[:MAX_CITATIONS], start=1)
    ]
    description = safe_answer or "GroundStack could not produce an answer."
    if citation_lines:
        description += "\n\nCitations\n" + "\n".join(citation_lines)
    description += (
        "\n\nAI-generated answer from retrieved GroundStack sources. "
        f"Grounding: `{grounding_status}`. Request: `{request_id}`."
    )
    if full_answer_url:
        description += f"\nFull answer: {full_answer_url}"
    embed = {
        "title": "GroundStack answer",
        "description": description[:EMBED_DESCRIPTION_LIMIT],
        "color": 0x2563EB,
    }
    components = []
    control_ids = control_ids or {}
    if control_ids:
        components = [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 3,
                        "label": "Helpful",
                        "custom_id": control_ids["helpful"],
                    },
                    {
                        "type": 2,
                        "style": 4,
                        "label": "Not helpful",
                        "custom_id": control_ids["not_helpful"],
                    },
                    {
                        "type": 2,
                        "style": 2,
                        "label": "View sources",
                        "custom_id": control_ids["sources"],
                    },
                    {
                        "type": 2,
                        "style": 2,
                        "label": "Ask a human",
                        "custom_id": control_ids["escalate"],
                    },
                ],
            }
        ]
        if full_answer_url:
            components[0]["components"].append(
                {"type": 2, "style": 5, "label": "Open full answer", "url": full_answer_url}
            )
    return DiscordRenderedAnswer(
        content="",
        embeds=[embed],
        components=components,
        allowed_mentions={"parse": []},
    )


def simple_message(text: str, *, ephemeral: bool = True) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": 4,
        "data": {
            "content": sanitize_markdown(text)[:DISCORD_CONTENT_LIMIT],
            "allowed_mentions": {"parse": []},
        },
    }
    if ephemeral:
        payload["data"]["flags"] = 64
    return payload


def deferred_message(*, ephemeral: bool) -> dict[str, Any]:
    data: dict[str, Any] = {"allowed_mentions": {"parse": []}}
    if ephemeral:
        data["flags"] = 64
    return {"type": 5, "data": data}
