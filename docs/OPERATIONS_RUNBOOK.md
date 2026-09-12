# Operations Runbook

## Start And Stop

```bash
make dev
# Ctrl+C when finished
make db-down
```

`make dev` starts and waits for PostgreSQL, applies migrations, and runs FastAPI and
Next.js. `make db-down` stops the database container without deleting its volume.

## Readiness

```bash
curl --fail http://localhost:8000/api/v1/health/live
curl --fail http://localhost:8000/api/v1/health/ready
docker compose ps
cd apps/api && .venv/bin/alembic current
```

Process health and dependency readiness are separate. A live API can still report degraded
readiness when PostgreSQL or the configured provider is unavailable.

## Recovery

- **Docker unavailable:** start Docker Desktop, run `docker info`, then `make dev`.
- **Database unavailable:** run `docker compose logs postgres`, then `make db-up`.
- **Migration mismatch:** run `make migrate` and `make migration-check`.
- **API unavailable:** verify port 8000 is free and run `make api-dev`.
- **Frontend unavailable:** verify port 3000 is free and run `make web-dev`.
- **Provider unavailable:** verify the private `LLM_*` configuration and provider health;
  do not switch to deterministic output for a real presentation.
- **Document stuck Processing:** inspect the API log by request/job ID, correct the cause, and
  use the existing Retry action.

Do not delete database volumes as a routine recovery step.
