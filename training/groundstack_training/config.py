from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _coerce_scalar(value: str) -> object:
    value = value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value in {"null", "None"}:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip('"').strip("'")


def load_yaml(path: str | Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore[import-not-found]

        loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return dict(loaded or {})
    except ModuleNotFoundError:
        result: dict[str, Any] = {}
        stack: list[tuple[int, dict[str, Any]]] = [(0, result)]
        for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            key, _, value = raw_line.strip().partition(":")
            while stack and indent < stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if value.strip():
                parent[key] = _coerce_scalar(value)
            else:
                child: dict[str, Any] = {}
                parent[key] = child
                stack.append((indent + 2, child))
        return result


def validate_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not config.get("base_model"):
        errors.append("base_model is required.")
    if config.get("base_model") == "meta-llama/Llama-3.2-3B-Instruct" and not config.get(
        "requires_llama_license_acknowledgement", True
    ):
        errors.append("Llama license acknowledgement must be required for the default base model.")
    qlora = dict(config.get("qlora", {}))
    if qlora.get("load_in_4bit") is not True:
        errors.append("qlora.load_in_4bit must be true.")
    if qlora.get("bnb_4bit_quant_type") != "nf4":
        errors.append("qlora.bnb_4bit_quant_type must be nf4.")
    lora = dict(config.get("lora", {}))
    if int(lora.get("rank", 0)) <= 0:
        errors.append("lora.rank must be positive.")
    if int(lora.get("alpha", 0)) <= 0:
        errors.append("lora.alpha must be positive.")
    training = dict(config.get("training", {}))
    if int(training.get("max_sequence_length", 0)) <= 0:
        errors.append("training.max_sequence_length must be positive.")
    dataset = dict(config.get("dataset", {}))
    if not dataset.get("source_path"):
        errors.append("dataset.source_path is required.")
    return errors


def dump_resolved_config(path: str | Path, config: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
