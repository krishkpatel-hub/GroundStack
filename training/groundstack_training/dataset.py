from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from groundstack_training.dedupe import deduplicate
from groundstack_training.prompting import load_prompt_template, to_chat_messages
from groundstack_training.schema import CanonicalExample, load_jsonl, write_jsonl
from groundstack_training.splitting import detect_split_leakage, split_examples
from groundstack_training.validation import validate_examples


def dataset_checksum(rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def prepare_dataset(
    *,
    source_path: str | Path,
    output_dir: str | Path,
    dataset_name: str,
    version: str,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
    near_duplicate_threshold: float,
    prompt_version: str,
) -> dict[str, Any]:
    examples = load_jsonl(source_path)
    validation = validate_examples(examples)
    if not validation.valid:
        raise ValueError("Dataset validation failed; run validate_dataset.py for details.")

    deduped = deduplicate(examples, near_duplicate_threshold=near_duplicate_threshold)
    assignments = split_examples(
        deduped.retained,
        seed=seed,
        train_ratio=train_ratio,
        validation_ratio=validation_ratio,
    )
    leaks = detect_split_leakage(deduped.retained, assignments)
    if leaks:
        raise ValueError(f"Split leakage detected for groups: {leaks}")

    template = load_prompt_template(prompt_version)
    rows: list[dict[str, Any]] = []
    for example in sorted(deduped.retained, key=lambda item: item.example_id):
        rows.append(
            {
                "example_id": example.example_id,
                "split": assignments[example.example_id],
                "messages": to_chat_messages(example, template),
                "answerability": example.answerability,
                "source_group": example.source_group,
                "category": example.category,
                "prompt_version": template.version,
                "prompt_checksum": template.checksum,
            }
        )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for split in ("train", "validation", "test"):
        write_jsonl(output / f"{split}.jsonl", [row for row in rows if row["split"] == split])
    write_jsonl(output / "all.jsonl", rows)
    checksum = dataset_checksum(rows)
    manifest = dataset_manifest(
        dataset_name=dataset_name,
        version=version,
        examples=examples,
        rows=rows,
        accepted_count=len(deduped.retained),
        rejected_count=len(deduped.rejected),
        dedupe_stats={
            "exact_duplicates": deduped.exact_duplicates,
            "near_duplicates": deduped.near_duplicates,
            "rejected": deduped.rejected,
        },
        split_method="source_group_category_hash",
        seed=seed,
        prompt_version=template.version,
        prompt_checksum=template.checksum,
        checksum=checksum,
    )
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest


def dataset_manifest(
    *,
    dataset_name: str,
    version: str,
    examples: list[CanonicalExample],
    rows: list[dict[str, Any]],
    accepted_count: int,
    rejected_count: int,
    dedupe_stats: dict[str, Any],
    split_method: str,
    seed: int,
    prompt_version: str,
    prompt_checksum: str,
    checksum: str,
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "semantic_version": version,
        "created_at": datetime.now(UTC).isoformat(),
        "source_example_count": len(examples),
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "train_count": sum(1 for row in rows if row["split"] == "train"),
        "validation_count": sum(1 for row in rows if row["split"] == "validation"),
        "test_count": sum(1 for row in rows if row["split"] == "test"),
        "answerability_distribution": dict(Counter(row["answerability"] for row in rows)),
        "category_distribution": dict(Counter(row["category"] for row in rows)),
        "provenance_distribution": dict(Counter(item.provenance.origin for item in examples)),
        "deduplication": dedupe_stats,
        "split_method": split_method,
        "random_seed": seed,
        "prompt_version": prompt_version,
        "prompt_checksum": prompt_checksum,
        "dataset_checksum": checksum,
        "generator_script_version": "prepare_dataset/v1",
        "git_commit": git_commit(),
    }
