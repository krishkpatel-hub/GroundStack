from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest


def _sync_database_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


def _maintenance_url(url: str) -> str:
    prefix, _, rest = url.rpartition("/")
    if not prefix or not rest:
        pytest.skip("DATABASE_URL is not a PostgreSQL URL with a database name.")
    return prefix + "/postgres"


def _run(
    command: list[str],
    *,
    env: Mapping[str, str] | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        capture_output=capture_output,
        text=True,
        env=dict(env) if env is not None else None,
        check=False,
    )
    if result.returncode != 0:
        output = "\n".join(
            part
            for part in [
                f"command: {' '.join(command)}",
                f"exit_code: {result.returncode}",
                f"stdout:\n{result.stdout.strip()}" if result.stdout else "stdout: <empty>",
                f"stderr:\n{result.stderr.strip()}" if result.stderr else "stderr: <empty>",
            ]
        )
        pytest.fail(output)
    return result


@pytest.mark.integration
def test_postgres_backup_restores_into_temporary_database(tmp_path: Path) -> None:
    if not all(shutil.which(command) for command in ["pg_dump", "pg_restore", "psql"]):
        pytest.skip("PostgreSQL client tools are not installed.")
    configured_url = os.getenv("DATABASE_URL")
    if not configured_url:
        pytest.skip("DATABASE_URL is required for the backup/restore drill.")

    source_url = _sync_database_url(configured_url)
    maintenance_url = _maintenance_url(source_url)
    restore_db = f"groundstack_restore_{os.getpid()}"
    restore_url = maintenance_url.rsplit("/", 1)[0] + f"/{restore_db}"
    root = Path(__file__).resolve().parents[4]

    try:
        _run(
            [
                "psql",
                maintenance_url,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                f'CREATE DATABASE "{restore_db}"',
            ],
        )
        backup_result = _run(
            [str(root / "scripts" / "backup_postgres.sh")],
            env={**os.environ, "DATABASE_URL": source_url, "BACKUP_DIR": str(tmp_path)},
        )
        backup = backup_result.stdout.strip().splitlines()[-1]
        assert Path(backup).is_file()
        _run(
            [str(root / "scripts" / "restore_postgres.sh")],
            env={
                **os.environ,
                "RESTORE_DATABASE_URL": restore_url,
                "BACKUP_FILE": backup,
            },
        )
        result = _run(
            [
                "psql",
                restore_url,
                "-tAc",
                "select count(*) from information_schema.tables where table_schema='public'",
            ],
        )
        assert int(result.stdout.strip()) > 0
    finally:
        subprocess.run(
            [
                "psql",
                maintenance_url,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                f'DROP DATABASE IF EXISTS "{restore_db}" WITH (FORCE)',
            ],
            check=False,
        )
