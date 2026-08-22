from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def file_checksum(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_model_manifest(**values: Any) -> dict[str, Any]:
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "training_method": "QLoRA supervised fine-tuning",
        "promotion_status": "created",
        "known_limitations": [
            "GroundStack retrieval remains responsible for current domain knowledge.",
            "No performance improvement is claimed without held-out evaluation.",
        ],
        "intended_use": "Grounded technical-support answers over supplied evidence.",
        "out_of_scope_uses": [
            "General-purpose advice without retrieved evidence.",
            "Automatic training on unreviewed user conversations.",
        ],
        "safety_considerations": [
            "Validate citations after generation.",
            "Reject examples with unknown provenance or secrets.",
        ],
    }
    manifest.update(values)
    return manifest


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
