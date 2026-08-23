from __future__ import annotations

import argparse
import json
from pathlib import Path

SCENARIOS = [
    "postgres_unavailable",
    "postgres_slow",
    "connection_pool_exhaustion",
    "redis_unavailable",
    "redis_slow",
    "provider_timeout",
    "provider_http_429",
    "provider_http_500",
    "stream_disconnect",
    "worker_termination",
    "worker_restart",
    "queue_backlog",
    "invalid_embedding_dimension",
    "empty_corpus",
    "corrupted_citation_metadata",
    "expired_discord_interaction_token",
    "duplicate_discord_interaction",
    "frontend_disconnect",
    "application_restart_during_traffic",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="List or validate local failure scenarios.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    payload = {
        "status": "defined",
        "validate_only": args.validate_only,
        "safety": "local_or_approved_test_infrastructure_only",
        "scenarios": [
            {
                "name": name,
                "restore_required": True,
                "records_detection_and_recovery_time": True,
            }
            for name in SCENARIOS
        ],
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
