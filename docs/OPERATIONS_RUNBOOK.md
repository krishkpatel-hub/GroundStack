# Operations Runbook

Version: `1.0.0-rc.1`

## Local Development

```bash
cp .env.example .env
make setup
make db-up
make migrate
make dev
```

## Release Verification

Run checks conservatively on memory-constrained laptops. Avoid Docker, browser E2E, Ollama, and
load tests simultaneously.

```bash
make lint
make typecheck
make test
npm run build --workspace apps/web
python scripts/check_migrations.py
```

## Demo Deployment

Use `deploy/demo-compose.yml` and `deploy/.env.demo.example`. Do not put secrets in repository
files. Run migrations as a one-off task before starting app containers.

## Incidents

- Database outage: restore DB connectivity, verify `/api/v1/health/ready`, then retry failed work.
- Redis outage: public demo quotas may fail closed when `DEMO_REDIS_REQUIRED=true`.
- Provider outage: disable demo chat or switch approved provider endpoint; do not fall back to a
  more expensive provider automatically.
- Prompt-injection report: quarantine source content, rerun security evals, and inspect generated
  answers for unsupported claims.
- Discord incident: disable guild config or `DISCORD_INTEGRATION_ENABLED`, rotate bot token if
  exposed, and verify interaction-token encryption key handling.

## Backups

Use `scripts/backup_postgres.sh` and `scripts/restore_postgres.sh`. Rollback is redeploying a prior
image plus forward database repair unless a restore drill has been approved.
