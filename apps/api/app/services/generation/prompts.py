import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

PROMPT_ROOT = Path(__file__).parents[2] / "prompts"


@dataclass(frozen=True)
class PromptTemplate:
    version: str
    system: str
    user: str
    checksum: str
    metadata: dict[str, object]


def load_prompt_template(version: str) -> PromptTemplate:
    root = PROMPT_ROOT / version
    system = (root / "system.txt").read_text(encoding="utf-8")
    user = (root / "user.txt").read_text(encoding="utf-8")
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    checksum = hashlib.sha256(
        (system + "\n---USER---\n" + user + "\n" + json.dumps(metadata, sort_keys=True)).encode(
            "utf-8"
        )
    ).hexdigest()
    return PromptTemplate(
        version=version, system=system, user=user, checksum=checksum, metadata=metadata
    )


def render_user_prompt(
    template: PromptTemplate, *, question: str, history: str, sources: str
) -> str:
    return (
        template.user.replace("{{question}}", question)
        .replace("{{history}}", history)
        .replace("{{sources}}", sources)
    )
