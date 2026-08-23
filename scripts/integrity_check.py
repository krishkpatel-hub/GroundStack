from __future__ import annotations

import argparse
import json
from pathlib import Path

CHECKS = [
    "no_duplicate_conversations",
    "no_duplicate_answers",
    "no_duplicate_feedback",
    "no_cross_user_conversation_access",
    "no_cross_guild_configuration_access",
    "no_orphaned_ingestion_records",
    "no_permanently_stuck_jobs",
    "no_citations_to_deleted_documents",
    "no_discord_training_candidates",
    "no_inconsistent_capacity_counters",
    "no_plaintext_interaction_tokens",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit GroundStack integrity check manifest.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    payload = {
        "status": "defined",
        "validate_only": args.validate_only,
        "checks": [{"name": check, "mode": "sql_or_api_probe"} for check in CHECKS],
        "limitations": [
            "This command defines post-load integrity checks.",
            "Database-backed execution should run only against local or approved "
            "test infrastructure.",
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
