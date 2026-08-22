from __future__ import annotations

import argparse
import json

from groundstack_training.config import load_yaml
from groundstack_training.preflight import hardware_preflight


def main() -> int:
    parser = argparse.ArgumentParser(description="Report QLoRA hardware and dependency readiness.")
    parser.add_argument("--config", default="training/configs/llama32_3b_qlora.yaml")
    parser.add_argument("--output", default="training/reports/preflight.json")
    args = parser.parse_args()
    config = load_yaml(args.config)
    report = hardware_preflight(
        base_model=str(config.get("base_model", "")), output_path=args.output
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
