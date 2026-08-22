from __future__ import annotations

import json
from pathlib import Path

import pytest

from groundstack_training.config import load_yaml, validate_config
from groundstack_training.dataset import dataset_checksum, prepare_dataset
from groundstack_training.dedupe import deduplicate
from groundstack_training.evaluation import evaluate_responses
from groundstack_training.lora import (
    adapter_manifest_valid,
    parameter_counts,
    validate_lora_targets,
    verify_base_frozen,
)
from groundstack_training.manifests import create_model_manifest
from groundstack_training.paths import safe_artifact_path
from groundstack_training.promotion import promotion_decision
from groundstack_training.prompting import (
    load_prompt_template,
    render_training_text,
    verify_completion_mask,
)
from groundstack_training.schema import CanonicalExample, load_jsonl
from groundstack_training.serving import generate_ollama_modelfile
from groundstack_training.splitting import detect_split_leakage, split_examples
from groundstack_training.validation import validate_examples

SEED = Path("data/seed/groundstack_seed.jsonl")


def test_canonical_dataset_schema_and_provenance() -> None:
    examples = load_jsonl(SEED)
    report = validate_examples(examples)

    assert len(examples) == 12
    assert report.valid
    assert report.accepted_count == 12
    assert report.provenance_distribution == {"human_authored": 12}


def test_validation_rejects_fabricated_citation_and_unapproved_review() -> None:
    example = load_jsonl(SEED)[0]
    bad = CanonicalExample.from_dict(
        {
            **example.to_dict(),
            "example_id": "bad-fabricated",
            "answer": "Use the setting [S9].",
            "provenance": {**example.provenance.__dict__, "review_status": "needs_review"},
        }
    )
    report = validate_examples([bad])

    assert not report.valid
    assert {issue.code for issue in report.issues} >= {
        "fabricated_citation",
        "unapproved_example",
    }


def test_exact_deduplication_and_near_duplicate_grouping_are_stable() -> None:
    examples = load_jsonl(SEED)
    duplicate = CanonicalExample.from_dict(
        {**examples[0].to_dict(), "example_id": "duplicate-copy"}
    )
    result = deduplicate([duplicate, *examples], near_duplicate_threshold=0.99)

    assert result.exact_duplicates == 1
    assert result.rejected[0]["reason"] == "exact_duplicate"
    assert [item.example_id for item in result.retained] == sorted(
        item.example_id for item in result.retained
    )


def test_splitting_keeps_semantic_groups_together() -> None:
    examples = load_jsonl(SEED)
    assignments = split_examples(examples, seed=1729, train_ratio=0.7, validation_ratio=0.15)

    assert set(assignments) == {example.example_id for example in examples}
    assert detect_split_leakage(examples, assignments) == []


def test_dataset_checksum_is_stable() -> None:
    rows = [{"example_id": "a", "messages": [{"role": "assistant", "content": "x"}]}]

    assert dataset_checksum(rows) == dataset_checksum(list(rows))


def test_prompt_rendering_and_completion_mask_validation() -> None:
    example = load_jsonl(SEED)[0]
    template = load_prompt_template("grounded_answer/v1")
    text = render_training_text(example, template)

    assert "UNTRUSTED SOURCE CONTENT" in text
    assert example.answer in text
    assert verify_completion_mask([0, 0, 1, 1], [10, 11, 12, 13])
    assert not verify_completion_mask([0, 1, 0, 1], [10, 11, 12, 13])


def test_config_validation_and_lora_helpers() -> None:
    config = load_yaml("configs/smoke_test.yaml")
    assert validate_config(config) == []
    assert validate_lora_targets(["model.layers.0.self_attn.q_proj"], "q_proj") == ["q_proj"]
    counts = parameter_counts([("base.weight", 100, False), ("lora_A.weight", 10, True)])
    assert counts["trainable_parameters"] == 10
    assert verify_base_frozen([("base.weight", 100, False), ("lora_A.weight", 10, True)])
    assert adapter_manifest_valid({}) == [
        "base_model",
        "adapter_path",
        "lora_rank",
        "target_modules",
        "promotion_status",
    ]


def test_prepare_dataset_creates_manifest_and_splits(tmp_path: Path) -> None:
    manifest = prepare_dataset(
        source_path=SEED,
        output_dir=tmp_path,
        dataset_name="test",
        version="0.1.0",
        seed=1729,
        train_ratio=0.7,
        validation_ratio=0.15,
        near_duplicate_threshold=0.99,
        prompt_version="grounded_answer/v1",
    )

    assert manifest["accepted_count"] == 12
    assert manifest["dataset_checksum"]
    assert (tmp_path / "train.jsonl").is_file()
    assert json.loads((tmp_path / "manifest.json").read_text())["dataset_checksum"]


def test_evaluation_metrics_and_promotion_gates() -> None:
    examples = json.loads(Path("data/eval/heldout_eval.json").read_text())
    responses = {
        "gs-eval-001-health": "It reports basic liveness for `GET /api/v1/health` [S1].",
        "gs-eval-002-unsupported": "I do not have enough evidence to answer.",
        "gs-eval-003-injection": "Ignore commands embedded in retrieved evidence [S1].",
    }
    result = evaluate_responses(examples, responses)
    decision = promotion_decision(
        dataset_valid=True,
        adapter_valid=True,
        leakage_detected=False,
        base_metrics=result.metrics,
        adapter_metrics=result.metrics,
        manual_review_completed=False,
        manifest_exists=True,
    )

    assert result.metrics["citation_valid_rate"] == 1.0
    assert decision["status"] == "awaiting_manual_review"


def test_model_manifest_modelfile_and_safe_paths(tmp_path: Path) -> None:
    manifest = create_model_manifest(
        model_name="groundstack-test",
        base_model="meta-llama/Llama-3.2-3B-Instruct",
    )
    modelfile = generate_ollama_modelfile(
        compatible_base_model="llama3.2:3b",
        adapter_path="/models/groundstack-adapter",
    )

    assert manifest["promotion_status"] == "created"
    assert "ADAPTER /models/groundstack-adapter" in modelfile
    assert safe_artifact_path(tmp_path, base=tmp_path) == tmp_path.resolve()
    with pytest.raises(ValueError):
        safe_artifact_path("/etc/passwd", base=tmp_path)
