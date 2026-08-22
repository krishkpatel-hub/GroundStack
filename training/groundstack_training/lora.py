from __future__ import annotations

from typing import Any


def validate_lora_targets(module_names: list[str], selected: str | list[str]) -> list[str]:
    if selected == "all-linear":
        suffixes = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        targets = sorted(
            {name.rsplit(".", 1)[-1] for name in module_names if name.endswith(tuple(suffixes))}
        )
    else:
        requested = [selected] if isinstance(selected, str) else selected
        targets = sorted(set(requested))
    missing = [
        target for target in targets if not any(name.endswith(target) for name in module_names)
    ]
    if missing:
        raise ValueError(f"LoRA target modules not present in base architecture: {missing}")
    return targets


def parameter_counts(parameters: list[tuple[str, int, bool]]) -> dict[str, float | int]:
    total = sum(count for _, count, _ in parameters)
    trainable = sum(count for _, count, requires_grad in parameters if requires_grad)
    return {
        "total_parameters": total,
        "trainable_parameters": trainable,
        "trainable_percent": round((trainable / total * 100), 6) if total else 0.0,
    }


def verify_base_frozen(
    parameters: list[tuple[str, int, bool]], adapter_markers: tuple[str, ...] = ("lora_",)
) -> bool:
    for name, _, requires_grad in parameters:
        if requires_grad and not any(marker in name for marker in adapter_markers):
            return False
    return True


def adapter_manifest_valid(manifest: dict[str, Any]) -> list[str]:
    required = ["base_model", "adapter_path", "lora_rank", "target_modules", "promotion_status"]
    return [field for field in required if field not in manifest or manifest[field] in {None, ""}]
