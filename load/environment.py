from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _run(command: list[str], *, timeout: int = 5) -> str:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return f"unavailable: {type(exc).__name__}"
    output = (completed.stdout or completed.stderr).strip()
    return output[:4000] if output else f"exit={completed.returncode}"


def git_commit() -> str:
    return _run(["git", "rev-parse", "HEAD"]).splitlines()[0]


def collect_environment() -> dict[str, Any]:
    disk = shutil.disk_usage(Path.cwd())
    return {
        "git_commit": git_commit(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        },
        "docker": _run(["docker", "info", "--format", "{{json .}}"]),
        "ollama": _run(["ollama", "ps"]),
        "listening_dev_ports": _run(
            ["lsof", "-nP", "-iTCP:3000", "-iTCP:8000", "-iTCP:5432", "-iTCP:6379", "-sTCP:LISTEN"]
        ),
        "memory_pressure": _run(["vm_stat"]),
    }


def write_environment(path: Path) -> None:
    path.write_text(json.dumps(collect_environment(), indent=2, sort_keys=True), encoding="utf-8")
