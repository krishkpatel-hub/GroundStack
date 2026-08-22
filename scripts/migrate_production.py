from __future__ import annotations

import os
import subprocess
from urllib.parse import urlparse


def _target() -> tuple[str, str]:
    url = os.getenv("DATABASE_DIRECT_URL") or os.getenv("DATABASE_URL", "")
    parsed = urlparse(url)
    return parsed.hostname or "unknown-host", parsed.path.lstrip("/") or "unknown-db"


def main() -> int:
    host, database = _target()
    print(f"Migration target host: {host}")
    print(f"Migration target database: {database}")
    if os.getenv("CONFIRM_PRODUCTION_MIGRATION") != "yes":
        print("Set CONFIRM_PRODUCTION_MIGRATION=yes to run alembic upgrade head.")
        return 2
    command = ["alembic", "-c", "apps/api/alembic.ini", "upgrade", "head"]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
