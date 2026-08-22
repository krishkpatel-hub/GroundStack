# Deployment Topologies

GroundStack supports two provider-neutral topologies.

## Single-Host Demo

Use `deploy/demo-compose.yml` for a single host with Caddy, Next.js, FastAPI, PostgreSQL with
pgvector, Redis, optional Ollama, and optional observability.

```bash
cp deploy/.env.demo.example deploy/.env.demo
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo build
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo up -d
```

The checked-in example uses local ports `8080` and `8443` with `PUBLIC_HOST=:80` so it can be
smoke-tested locally at `http://localhost:8080`. For a public TLS host, set `PUBLIC_HOST` and
`PUBLIC_API_BASE_URL` to the real HTTPS domain and use ports `80` and `443`.

Only Caddy publishes public ports. PostgreSQL, Redis, inference, and application services stay on
internal Docker networks. Caddy is configured to preserve SSE streaming for `/api/*`.

Enable optional local inference or observability with Compose profiles:

```bash
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo --profile ollama up -d
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo --profile observability up -d
```

Prometheus stays on the internal observability network and reads the API metrics token from
`METRICS_INTERNAL_TOKEN`. Example CPU and memory limits are in `deploy/resources.example.yml`; use
it as an override if the host needs explicit caps:

```bash
docker compose -f deploy/demo-compose.yml -f deploy/resources.example.yml --env-file deploy/.env.demo up -d
```

Run migrations as a one-off release task before replacing API replicas:

```bash
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo run --rm api alembic upgrade head
```

## Managed Production

Use the same API and web images with:

- Managed PostgreSQL that supports pgvector.
- Managed Redis.
- External Ollama, vLLM, or OpenAI-compatible inference.
- Managed TLS/load balancer or reverse proxy.
- External object storage for backups if configured by the operator.

GroundStack is not yet a fully isolated multi-tenant knowledge platform. The knowledge base remains
an admin-managed shared corpus.
