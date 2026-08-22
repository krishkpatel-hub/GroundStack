from __future__ import annotations

import argparse
import json
from pathlib import Path

from groundstack_training.evaluation import evaluate_responses


def main() -> int:
    parser = argparse.ArgumentParser(description="Format base-vs-adapter comparison reports.")
    parser.add_argument("--examples", default="training/data/eval/heldout_eval.json")
    parser.add_argument("--base-responses", required=False)
    parser.add_argument("--adapter-responses", required=False)
    parser.add_argument("--output", default="training/reports/base_vs_adapter.json")
    args = parser.parse_args()
    examples = json.loads(Path(args.examples).read_text(encoding="utf-8"))
    base = (
        json.loads(Path(args.base_responses).read_text(encoding="utf-8"))
        if args.base_responses
        else {}
    )
    adapter = (
        json.loads(Path(args.adapter_responses).read_text(encoding="utf-8"))
        if args.adapter_responses
        else {}
    )
    payload = {
        "base": evaluate_responses(examples, base).metrics if base else None,
        "adapter": evaluate_responses(examples, adapter).metrics if adapter else None,
        "manual_review": [
            {
                "example_id": example["example_id"],
                "response_a": base.get(example["example_id"], ""),
                "response_b": adapter.get(example["example_id"], ""),
                "label_hidden": True,
            }
            for example in examples
        ],
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
