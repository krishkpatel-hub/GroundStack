from __future__ import annotations

import argparse
import json

from groundstack_training.config import load_yaml
from groundstack_training.dataset import prepare_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare GroundStack TRL-format dataset.")
    parser.add_argument("--config", default="training/configs/smoke_test.yaml")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    config = load_yaml(args.config)
    dataset = dict(config["dataset"])
    split = dict(config.get("split", {}))
    output_dir = args.output_dir or dataset.get("output_dir", "training/data/processed/smoke")
    manifest = prepare_dataset(
        source_path=dataset["source_path"],
        output_dir=output_dir,
        dataset_name=dataset["name"],
        version=str(dataset["version"]),
        seed=int(split.get("seed", 42)),
        train_ratio=float(split.get("train_ratio", 0.7)),
        validation_ratio=float(split.get("validation_ratio", 0.15)),
        near_duplicate_threshold=float(dataset.get("near_duplicate_threshold", 0.94)),
        prompt_version=str(config.get("prompt_version", "grounded_answer/v1")),
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
