from __future__ import annotations

import argparse
import json

from groundstack_training.manifests import create_model_manifest, write_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a GroundStack adapter model manifest.")
    parser.add_argument("--model-name", default="groundstack-llama32-3b-adapter")
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--base-model", default="meta-llama/Llama-3.2-3B-Instruct")
    parser.add_argument("--dataset-version", default="groundstack-seed-dev/0.1.0")
    parser.add_argument("--dataset-checksum", default=None)
    parser.add_argument("--adapter-checksum", default=None)
    parser.add_argument("--promotion-status", default="created")
    parser.add_argument("--output", default="training/reports/model_manifest.json")
    args = parser.parse_args()
    manifest = create_model_manifest(
        model_name=args.model_name,
        version=args.version,
        base_model=args.base_model,
        base_model_revision=None,
        llama_license_reference="https://www.llama.com/llama-downloads/",
        lora_configuration=None,
        dataset_version=args.dataset_version,
        dataset_checksum=args.dataset_checksum,
        training_example_counts=None,
        evaluation_example_counts=None,
        training_hardware=None,
        training_duration_seconds=None,
        dependency_versions=None,
        prompt_version="grounded_answer/v1",
        deterministic_evaluation_results=None,
        manual_review_status="not_started",
        adapter_artifact_checksum=args.adapter_checksum,
        promotion_status=args.promotion_status,
    )
    write_manifest(args.output, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
