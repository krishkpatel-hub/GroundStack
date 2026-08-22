from __future__ import annotations

import argparse
import json
from pathlib import Path

from groundstack_training.evaluation import evaluate_responses


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic GroundStack responses.")
    parser.add_argument("--examples", default="training/data/eval/heldout_eval.json")
    parser.add_argument("--responses", required=True)
    parser.add_argument("--output", default="training/reports/evaluation.json")
    args = parser.parse_args()
    examples = json.loads(Path(args.examples).read_text(encoding="utf-8"))
    responses = json.loads(Path(args.responses).read_text(encoding="utf-8"))
    result = evaluate_responses(examples, responses)
    payload = {"metrics": result.metrics, "rows": result.rows}
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
