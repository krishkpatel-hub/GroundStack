from __future__ import annotations

import argparse
import json
from pathlib import Path

from groundstack_training.serving import validate_adapter_artifact


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PEFT adapter artifact structure.")
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--output", default="training/reports/adapter_validation.json")
    args = parser.parse_args()
    missing = validate_adapter_artifact(args.adapter_path)
    payload = {"valid": not missing, "adapter_path": args.adapter_path, "missing": missing}
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
