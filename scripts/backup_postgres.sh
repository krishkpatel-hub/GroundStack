#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_DIR="${BACKUP_DIR:-backups/postgres}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${BACKUP_DIR}/groundstack-${STAMP}.dump.gz"

mkdir -p "${BACKUP_DIR}"
pg_dump "${DATABASE_URL}" --format=custom --no-owner --no-privileges | gzip -9 > "${DEST}"

if [[ -n "${BACKUP_ENCRYPTION_KEY_FILE:-}" ]]; then
  openssl enc -aes-256-cbc -salt -pbkdf2 -in "${DEST}" -out "${DEST}.enc" -pass "file:${BACKUP_ENCRYPTION_KEY_FILE}"
  rm "${DEST}"
  DEST="${DEST}.enc"
fi

find "${BACKUP_DIR}" -type f -name 'groundstack-*' -mtime +"${RETENTION_DAYS}" -print -delete
echo "${DEST}"
