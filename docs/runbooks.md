# Operational Runbooks

## Initial Deployment

1. Configure `deploy/.env.demo` from `deploy/.env.demo.example`.
2. Build images: `docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo build`.
3. Run migrations once: `docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo run --rm api alembic upgrade head`.
4. Start: `docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo up -d`.

## Routine Release

Run the full quality gate, build images, run migrations as a one-off task, then replace app
containers. Keep the previous image tags until health checks pass.

## Rollback

Redeploy the previous image tags. If a migration is irreversible, perform a forward repair rather
than destructive rollback unless a restore drill has been approved.

## Database Backup And Restore

Backup: `DATABASE_URL=... scripts/backup_postgres.sh`.
Restore to a new database: `RESTORE_DATABASE_URL=... BACKUP_FILE=... scripts/restore_postgres.sh`.

## Secret Rotation

Rotate OIDC client secrets, metrics token, database password, and backup encryption keys one at a
time. Restart API containers after secret changes and verify `/api/v1/health`.

## Database Outage

Check managed database status or `docker compose ps postgres`; restore connectivity before
restarting API replicas. Do not run migrations during an outage.

## Redis Outage

GroundStack can keep serving core routes that do not require Redis-backed quotas. Restore Redis and
watch rate-limit behavior before increasing traffic.

## Inference Provider Outage

Switch `LLM_BASE_URL` or provider configuration to a healthy endpoint, then verify chat streaming
and grounded citation validation.

## Embedding Model Migration

Create a migration plan for embedding dimensions, reingest or rebuild vectors, run retrieval eval,
and only then promote the new embedding model.

## Compromised API Credential

Revoke the credential at the provider, rotate affected secrets, invalidate sessions where possible,
and review logs with token redaction enabled.

## High Latency Or Overload

Lower chat concurrency, inspect backpressure metrics, run `make load-smoke-fake`, and scale the API
or inference provider only after confirming database health.

## Prompt-Injection Incident

Remove or quarantine the source document, re-run security evaluation, and inspect affected
conversations for unsupported claims.

## Remove Document From Corpus

Disable or delete the source through an admin workflow, rebuild affected indexes, run retrieval
evaluation, and document the removal reason.
