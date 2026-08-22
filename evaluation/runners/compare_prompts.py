from __future__ import annotations

import json
import os
from pathlib import Path

from groundstack_eval.manifest import write_report


def main() -> int:
    prompts = [
        os.getenv("GENERATION_PROMPT_VERSION", "grounded_answer/v1"),
        os.getenv("GENERATION_PROMPT_CANDIDATE", "grounded_answer/v1"),
    ]
    payload = {
        "comparison_type": "prompt_configuration",
        "prompts": prompts,
        "status": "manifest_only",
        "note": "Run each prompt through evaluation/runners/run_eval.py and compare reports.",
    }
    destination = Path("evaluation/reports/prompt_comparison_manifest.json")
    write_report(destination, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
