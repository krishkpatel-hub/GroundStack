from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


def _sync_database_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


def _maintenance_url(url: str) -> str:
    prefix, _, rest = url.rpartition("/")
    if not prefix or not rest:
        pytest.skip("DATABASE_URL is not a PostgreSQL URL with a database name.")
    return prefix + "/postgres"


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
        subprocess.run(
            [
                "psql",
                maintenance_url,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                f'CREATE DATABASE "{restore_db}"',
            ],
            check=True,
        )
        backup = (
            subprocess.run(
                [str(root / "scripts" / "backup_postgres.sh")],
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "DATABASE_URL": source_url, "BACKUP_DIR": str(tmp_path)},
            )
            .stdout.strip()
            .splitlines()[-1]
        )
        subprocess.run(
            [str(root / "scripts" / "restore_postgres.sh")],
            check=True,
            env={
                **os.environ,
                "RESTORE_DATABASE_URL": restore_url,
                "BACKUP_FILE": backup,
            },
        )
        result = subprocess.run(
            [
                "psql",
                restore_url,
                "-tAc",
                "select count(*) from information_schema.tables where table_schema='public'",
            ],
            check=True,
            capture_output=True,
            text=True,
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
