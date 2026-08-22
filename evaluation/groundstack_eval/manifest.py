from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
    except Exception:
        return "unknown"


def build_manifest(*, suites: list[str], dataset: Path) -> dict[str, object]:
    return {
        "run_id": datetime.now(UTC).strftime("eval-%Y%m%dT%H%M%SZ"),
        "suite_names": suites,
        "dataset_version": dataset.name,
        "dataset_checksum": checksum(dataset),
        "model": {
            "provider": os.getenv("LLM_PROVIDER", "unknown"),
            "model": os.getenv("LLM_MODEL", "unknown"),
            "variant": os.getenv("LLM_MODEL_VARIANT", "base"),
            "adapter_version": os.getenv("LLM_ADAPTER_VERSION", ""),
        },
        "retrieval": {
            "embedding_model": os.getenv("EMBEDDING_MODEL_NAME", ""),
            "reranker_model": os.getenv("RERANKER_MODEL_NAME", ""),
            "algorithm_version": os.getenv("RETRIEVAL_ALGORITHM_VERSION", "hybrid-rrf-ce-v1"),
        },
        "prompt_version": os.getenv("GENERATION_PROMPT_VERSION", "grounded_answer/v1"),
        "git_commit": git_commit(),
        "started_at": datetime.now(UTC).isoformat(),
    }


def write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
