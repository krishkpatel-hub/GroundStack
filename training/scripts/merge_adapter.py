from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge an adapter into a new model directory.")
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.parse_args()
    raise SystemExit(
        "Adapter merging requires a CUDA/CPU host with enough RAM and disk plus PEFT/Transformers. "
        "This script intentionally refuses to run until implemented on that host "
        "with explicit paths."
    )


if __name__ == "__main__":
    raise SystemExit(main())
