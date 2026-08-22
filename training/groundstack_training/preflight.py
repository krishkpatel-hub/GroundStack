from __future__ import annotations

import importlib.metadata
import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


def _version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def hardware_preflight(*, base_model: str, output_path: str | Path | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {
        "operating_system": platform.platform(),
        "python_version": sys.version.split()[0],
        "packages": {
            "torch": _version("torch"),
            "transformers": _version("transformers"),
            "trl": _version("trl"),
            "peft": _version("peft"),
            "accelerate": _version("accelerate"),
            "bitsandbytes": _version("bitsandbytes"),
            "datasets": _version("datasets"),
        },
        "base_model": base_model,
        "disk_free_bytes": shutil.disk_usage(Path.cwd()).free,
    }
    try:
        import torch  # type: ignore[import-not-found]

        cuda_available = bool(torch.cuda.is_available())
        report["cuda"] = {
            "available": cuda_available,
            "version": torch.version.cuda,
            "device_count": torch.cuda.device_count() if cuda_available else 0,
            "bf16_supported": bool(torch.cuda.is_bf16_supported()) if cuda_available else False,
            "gpus": [],
        }
        if cuda_available:
            for index in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(index)
                report["cuda"]["gpus"].append(
                    {
                        "name": props.name,
                        "total_memory_bytes": props.total_memory,
                    }
                )
    except Exception as exc:
        report["cuda"] = {"available": False, "error": str(exc), "gpus": []}

    compatible = bool(report["cuda"].get("available")) and bool(
        report["packages"].get("bitsandbytes")
    )
    report["estimated_training_compatibility"] = (
        "cuda_qlora_ready" if compatible else "dataset_and_tests_only"
    )
    if "meta-llama/" in base_model:
        report["base_model_access"] = (
            "requires Hugging Face authentication and accepted Llama license"
        )
    else:
        report["base_model_access"] = "check provider permissions"
    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report
