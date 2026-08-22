from __future__ import annotations

import argparse
from pathlib import Path

from groundstack_training.serving import generate_ollama_modelfile


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an Ollama Modelfile template.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--output", default="training/reports/Modelfile.groundstack")
    args = parser.parse_args()
    content = generate_ollama_modelfile(
        compatible_base_model=args.base, adapter_path=args.adapter_path
    )
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
