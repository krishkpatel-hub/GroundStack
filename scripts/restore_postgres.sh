#!/usr/bin/env bash
set -euo pipefail

: "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL must target a new database}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"

if [[ "${ALLOW_OVERWRITE_RESTORE:-false}" != "true" ]]; then
  if psql "${RESTORE_DATABASE_URL}" -tAc "select 1" >/dev/null 2>&1; then
    existing="$(psql "${RESTORE_DATABASE_URL}" -tAc "select count(*) from information_schema.tables where table_schema='public'")"
    if [[ "${existing}" != "0" ]]; then
      echo "Refusing to restore into a non-empty database. Set ALLOW_OVERWRITE_RESTORE=true to override." >&2
      exit 2
    fi
  fi
fi

if [[ "${BACKUP_FILE}" == *.enc ]]; then
  : "${BACKUP_ENCRYPTION_KEY_FILE:?BACKUP_ENCRYPTION_KEY_FILE is required for encrypted backups}"
  openssl enc -d -aes-256-cbc -pbkdf2 -in "${BACKUP_FILE}" -pass "file:${BACKUP_ENCRYPTION_KEY_FILE}" | gunzip | pg_restore --dbname="${RESTORE_DATABASE_URL}" --clean --if-exists
else
  gunzip -c "${BACKUP_FILE}" | pg_restore --dbname="${RESTORE_DATABASE_URL}" --clean --if-exists
fi
