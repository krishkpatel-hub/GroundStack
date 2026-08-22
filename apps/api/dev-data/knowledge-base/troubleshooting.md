# GroundStack Troubleshooting

## Database Is Offline

If the connection indicator shows the database as offline, run `docker compose ps`
and confirm the `groundstack-postgres` container is healthy.

## Migrations Fail

Migration failures usually mean the database is not reachable or the `vector`
extension image is not running. Restart the database container and rerun:

```bash
make migrate
```

## Empty Knowledge Base

The Knowledge Base page only displays documents that were ingested through the
API or CLI. Use `make ingest-sample` to load the local development examples.
