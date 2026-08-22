from __future__ import annotations

import hashlib
from collections import defaultdict

from groundstack_training.schema import CanonicalExample

SPLITS = ("train", "validation", "test")


def semantic_group(example: CanonicalExample) -> str:
    return f"{example.source_group}:{example.category}"


def split_examples(
    examples: list[CanonicalExample],
    *,
    seed: int,
    train_ratio: float,
    validation_ratio: float,
) -> dict[str, str]:
    groups: dict[str, list[CanonicalExample]] = defaultdict(list)
    for example in examples:
        groups[semantic_group(example)].append(example)

    ordered_groups = sorted(
        groups,
        key=lambda group: hashlib.sha256(f"{seed}:{group}".encode()).hexdigest(),
    )
    assignments: dict[str, str] = {}
    total = len(examples)
    train_target = max(1, round(total * train_ratio))
    validation_target = max(1, round(total * validation_ratio)) if total >= 3 else 0
    counts = {"train": 0, "validation": 0, "test": 0}
    for group in ordered_groups:
        size = len(groups[group])
        if counts["train"] + size <= train_target:
            split = "train"
        elif counts["validation"] + size <= validation_target:
            split = "validation"
        else:
            split = "test"
        counts[split] += size
        for example in groups[group]:
            assignments[example.example_id] = split
    return assignments


def detect_split_leakage(
    examples: list[CanonicalExample], assignments: dict[str, str]
) -> list[str]:
    seen: dict[str, str] = {}
    leaks: list[str] = []
    for example in examples:
        group = semantic_group(example)
        split = assignments[example.example_id]
        if group in seen and seen[group] != split:
            leaks.append(group)
        seen[group] = split
    return sorted(set(leaks))
