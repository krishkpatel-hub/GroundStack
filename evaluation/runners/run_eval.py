from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from groundstack_eval.manifest import build_manifest, write_report
from groundstack_eval.metrics import evaluate_case


def load_cases(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic GroundStack evaluation suites.")
    parser.add_argument("--dataset", default="evaluation/datasets/regression_cases.jsonl")
    parser.add_argument("--suite", action="append", default=[])
    args = parser.parse_args()
    suites = args.suite or ["all"]
    dataset = Path(args.dataset)
    cases = load_cases(dataset)
    if "all" not in suites:
        cases = [case for case in cases if case.get("suite") in suites]
    manifest = build_manifest(suites=suites, dataset=dataset)
    results = [evaluate_case(case) for case in cases]
    counts = Counter("passed" if result.passed else "failed" for result in results)
    report = {
        "manifest": {**manifest, "completed_at": datetime.now(UTC).isoformat()},
        "aggregate_metrics": {
            "case_count": len(results),
            "passed_count": counts["passed"],
            "failed_count": counts["failed"],
            "pass_rate": round(counts["passed"] / len(results), 4) if results else 0.0,
        },
        "results": [result.__dict__ for result in results],
    }
    destination = Path("evaluation/reports") / f"{manifest['run_id']}.json"
    write_report(destination, report)
    print(json.dumps({"report": str(destination), **report["aggregate_metrics"]}, indent=2))
    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
