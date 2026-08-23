from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path


def check(name: str, ok: bool, detail: str = "") -> bool:
    print(f"{'PASS' if ok else 'FAIL'} {name}{': ' + detail if detail else ''}")
    return ok


def command_ok(command: list[str]) -> bool:
    return (
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        == 0
    )


def tcp_ok(url: str) -> bool:
    if "://" in url:
        url = url.split("://", 1)[1]
    host_port = url.split("/", 1)[0].rsplit("@", 1)[-1]
    host, _, port = host_port.partition(":")
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, int(port)), timeout=3):
            return True
    except OSError:
        return False


def no_secret_files() -> bool:
    blocked = [".env", "id_rsa", "private.key"]
    return not any(Path(item).exists() for item in blocked)


def main() -> int:
    env = os.getenv("APP_ENV", "")
    checks = [
        check("APP_ENV", env in {"demo", "production"}, "set APP_ENV=demo or production"),
        check("dev auth bypass disabled", os.getenv("DEV_AUTH_BYPASS_ENABLED") == "false"),
        check(
            "exact CORS",
            bool(os.getenv("CORS_ORIGINS")) and "*" not in os.getenv("CORS_ORIGINS", ""),
        ),
        check(
            "trusted hosts",
            bool(os.getenv("TRUSTED_HOSTS")) and "*" not in os.getenv("TRUSTED_HOSTS", ""),
        ),
        check("metrics token present", bool(os.getenv("METRICS_INTERNAL_TOKEN"))),
        check("migration history", command_ok([sys.executable, "scripts/check_migrations.py"])),
        check("no local secret files", no_secret_files()),
    ]
    database_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL")
    if database_url:
        checks.append(check("database tcp", tcp_ok(database_url)))
    if redis_url:
        checks.append(check("redis tcp", tcp_ok(redis_url)))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
