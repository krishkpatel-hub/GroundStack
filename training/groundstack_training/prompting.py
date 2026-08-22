from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from groundstack_training.paths import PROMPT_ROOT
from groundstack_training.schema import CanonicalExample, Evidence


@dataclass(frozen=True)
class PromptTemplate:
    version: str
    system: str
    user: str
    checksum: str
    metadata: dict[str, object]


def load_prompt_template(version: str = "grounded_answer/v1") -> PromptTemplate:
    root = PROMPT_ROOT / version
    system = (root / "system.txt").read_text(encoding="utf-8").strip()
    user = (root / "user.txt").read_text(encoding="utf-8").strip()
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    checksum = hashlib.sha256(
        (
            version + "\n" + system + "\n" + user + "\n" + json.dumps(metadata, sort_keys=True)
        ).encode("utf-8")
    ).hexdigest()
    return PromptTemplate(
        version=version, system=system, user=user, checksum=checksum, metadata=metadata
    )


def evidence_block(evidence: Evidence) -> str:
    return (
        f'<source id="{evidence.citation_id}" title="{evidence.title}" '
        f'section="{evidence.section}">\n'
        f"UNTRUSTED SOURCE CONTENT\n{evidence.content}\n</source>"
    )


def render_user_prompt(template: PromptTemplate, example: CanonicalExample) -> str:
    sources = "\n\n".join(evidence_block(item) for item in example.evidence)
    if not sources:
        sources = "No retrieved evidence."
    return (
        template.user.replace("{{question}}", example.question)
        .replace("{{history}}", "No prior conversation.")
        .replace("{{sources}}", sources)
    )


def to_chat_messages(example: CanonicalExample, template: PromptTemplate) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": template.system},
        {"role": "user", "content": render_user_prompt(template, example)},
        {"role": "assistant", "content": example.answer},
    ]


def render_training_text(example: CanonicalExample, template: PromptTemplate) -> str:
    messages = to_chat_messages(example, template)
    return "\n\n".join(f"<|{item['role']}|>\n{item['content']}" for item in messages)


def verify_completion_mask(mask: list[int], labels: list[int]) -> bool:
    if len(mask) != len(labels) or not mask:
        return False
    completion_positions = [index for index, value in enumerate(mask) if value == 1]
    if not completion_positions:
        return False
    first = completion_positions[0]
    return all(value == 0 for value in mask[:first]) and all(value == 1 for value in mask[first:])
