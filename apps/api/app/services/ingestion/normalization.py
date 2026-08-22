import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [line.rstrip() for line in normalized.split("\n")]
    collapsed: list[str] = []
    blank_seen = False
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            blank_seen = False
            collapsed.append(line)
            continue
        if in_fence:
            collapsed.append(line)
            continue
        if not stripped:
            if not blank_seen:
                collapsed.append("")
            blank_seen = True
            continue
        blank_seen = False
        collapsed.append(re.sub(r"[ \t]+", " ", line).strip())
    return "\n".join(collapsed).strip()
