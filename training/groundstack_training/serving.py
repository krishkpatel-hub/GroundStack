from __future__ import annotations

from pathlib import Path


def generate_ollama_modelfile(*, compatible_base_model: str, adapter_path: str) -> str:
    if not compatible_base_model.strip():
        raise ValueError("compatible_base_model is required.")
    if not adapter_path.strip():
        raise ValueError("adapter_path is required.")
    return (
        f"FROM {compatible_base_model}\n"
        f"ADAPTER {adapter_path}\n"
        'PARAMETER stop "<|eot_id|>"\n'
        'SYSTEM "You are GroundStack, a grounded technical support assistant."\n'
    )


def validate_adapter_artifact(path: str | Path) -> list[str]:
    root = Path(path)
    missing = []
    for filename in ("adapter_config.json",):
        if not (root / filename).is_file():
            missing.append(filename)
    has_weights = any(
        (root / filename).is_file()
        for filename in ("adapter_model.safetensors", "adapter_model.bin")
    )
    if not has_weights:
        missing.append("adapter_model.safetensors or adapter_model.bin")
    return missing
