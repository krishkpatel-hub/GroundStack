from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

REQUIRED_TOP_LEVEL = {
    "configuration",
    "environment",
    "results",
    "percentiles",
    "failure_counts",
    "recovery_times",
    "resource_use",
    "evidence_paths",
    "git_commit",
}


def validate_payload(payload: dict[str, object]) -> list[str]:
    missing = sorted(REQUIRED_TOP_LEVEL - set(payload))
    errors = [f"missing {item}" for item in missing]
    if not isinstance(payload.get("evidence_paths", []), list):
        errors.append("evidence_paths must be a list")
    return errors


def baseline_payload() -> dict[str, object]:
    return {
        "configuration": {
            "workload_profile": "not_run",
            "provider_mode": "fake",
            "concurrency": 0,
            "spawn_rate": 0,
            "warmup_duration_seconds": 0,
            "success_criteria": [],
        },
        "environment": {"date": datetime.now(UTC).isoformat()},
        "results": {
            "total_requests": 0,
            "successful_answers": 0,
            "grounded_answers": 0,
            "insufficient_evidence": 0,
        },
        "percentiles": {"p50_ms": None, "p95_ms": None, "p99_ms": None},
        "failure_counts": {},
        "recovery_times": {},
        "resource_use": {},
        "evidence_paths": [],
        "git_commit": "not_recorded",
        "limitations": ["Generated schema baseline; no traffic result."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or emit GroundStack capacity evidence.")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    payload = (
        json.loads(args.input.read_text(encoding="utf-8")) if args.input else baseline_payload()
    )
    errors = validate_payload(payload)
    if errors:
        for error in errors:
            print(error)
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    elif not args.validate_only:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
