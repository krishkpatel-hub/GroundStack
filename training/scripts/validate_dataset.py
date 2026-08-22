from __future__ import annotations

import argparse
import json
from pathlib import Path

from groundstack_training.schema import load_jsonl
from groundstack_training.validation import validate_examples


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical GroundStack examples.")
    parser.add_argument("--input", default="training/data/seed/groundstack_seed.jsonl")
    parser.add_argument("--report", default="training/reports/dataset_validation.json")
    args = parser.parse_args()

    examples = load_jsonl(args.input)
    report = validate_examples(examples)
    payload = {
        "valid": report.valid,
        "accepted_count": report.accepted_count,
        "rejected_count": report.rejected_count,
        "issues": [issue.__dict__ for issue in report.issues],
        "answerability_distribution": report.answerability_distribution,
        "category_distribution": report.category_distribution,
        "provenance_distribution": report.provenance_distribution,
    }
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
