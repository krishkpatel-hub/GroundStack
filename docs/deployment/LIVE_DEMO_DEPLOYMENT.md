# Live Demo Deployment Runbook

This runbook prepares a recruiter-accessible GroundStack demo using Vercel, Render, Neon,
Upstash Redis, and an OpenAI-compatible hosted LLaMA provider. Use demo data only. Do not
enter secrets into source control, GitHub issues, PR comments, or chat.

## Current Blocker

Deployment requires owner access to Vercel, Render, Neon, Upstash, and the selected inference
provider. No authenticated deployment CLI or connector is configured in this workspace, so the
repository can only provide safe manifests and instructions until those services exist.

## Service Plan Choices

- Vercel: Hobby plan.
- Render: Free web service using `render.yaml`.
- Neon: Free plan project with PostgreSQL and pgvector.
- Upstash: Free Redis database.
- LLM provider: an OpenAI-compatible hosted LLaMA endpoint on a free or already-approved plan.

Stop before selecting any paid tier, adding a card where it is not required, enabling autoscaling
with billing impact, or increasing limits beyond the free tier.

## Expected URLs

Replace these placeholders after the services are created:

- Frontend URL: `https://<vercel-project>.vercel.app`
- Backend URL: `https://groundstack-api.onrender.com`
- Neon pooled host: `<neon-endpoint>-pooler.<region>.neon.tech`
- Upstash Redis host: `<upstash-endpoint>`
- LLM base URL: `https://<provider-host>/v1`

## Vercel Environment

Public values:

| Key                        | Value                                  |
| -------------------------- | -------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://groundstack-api.onrender.com` |
| `NEXT_PUBLIC_SITE_URL`     | `https://<vercel-project>.vercel.app`  |

Generated non-secret configuration:

| Setting           | Value                                            |
| ----------------- | ------------------------------------------------ |
| Project name      | `groundstack-demo`                               |
| Framework preset  | Next.js                                          |
| Root directory    | `apps/web`                                       |
| Install command   | `cd ../.. && npm ci`                             |
| Build command     | `cd ../.. && npm run build --workspace apps/web` |
| Output directory  | `.next`                                          |
| Production branch | `main` after the deployment PR is merged         |
| Preview branch    | `deploy/live-demo` before merge                  |

Owner-supplied secrets:

None for the Vercel frontend. Do not add API keys to Vercel unless a future server-side frontend
feature explicitly requires them.

## Render Environment

`render.yaml` defines one API web service and intentionally does not deploy a Discord worker.

Public values:

| Key                           | Value               |
| ----------------------------- | ------------------- |
| `APP_ENV`                     | `demo`              |
| `ALLOW_ANONYMOUS_DEMO`        | `true`              |
| `DEV_AUTH_BYPASS_ENABLED`     | `false`             |
| `DOCS_ENABLED`                | `false`             |
| `DEMO_CHAT_ENABLED`           | `true`              |
| `DEMO_REDIS_REQUIRED`         | `true`              |
| `DB_SSL_REQUIRED`             | `true`              |
| `DISCORD_INTEGRATION_ENABLED` | `false`             |
| `DISCORD_ALLOW_DMS`           | `false`             |
| `LLM_PROVIDER`                | `openai_compatible` |
| `REDIS_KEY_NAMESPACE`         | `groundstack`       |

Generated non-secret configuration:

| Key                                    | Value                                                    |
| -------------------------------------- | -------------------------------------------------------- |
| `CORS_ORIGINS`                         | `https://<vercel-project>.vercel.app`                    |
| `TRUSTED_HOSTS`                        | `groundstack-api.onrender.com,<custom-api-host-if-used>` |
| `PUBLIC_API_BASE_URL`                  | `https://groundstack-api.onrender.com`                   |
| `DEMO_REQUEST_LIMIT_PER_MINUTE`        | `4`                                                      |
| `DEMO_DAILY_QUESTION_LIMIT`            | `40`                                                     |
| `DEMO_DAILY_TOKEN_LIMIT`               | `10000`                                                  |
| `DEMO_MAX_QUESTION_LENGTH`             | `500`                                                    |
| `DEMO_MAX_CONTEXT_TOKENS`              | `2200`                                                   |
| `DEMO_PROVIDER_FAILURE_THRESHOLD`      | `3`                                                      |
| `DEMO_PROVIDER_FAILURE_WINDOW_SECONDS` | `300`                                                    |
| `DEMO_UPLOAD_LIMIT_BYTES`              | `0`                                                      |
| `DEMO_MAX_CONVERSATIONS`               | `3`                                                      |
| `LLM_TIMEOUT_SECONDS`                  | `45`                                                     |
| `LLM_REQUEST_TIMEOUT_SECONDS`          | `45`                                                     |
| `LLM_MAX_OUTPUT_TOKENS`                | `500`                                                    |
| `LLM_MAX_CONCURRENT_REQUESTS`          | `2`                                                      |
| `LLM_MAX_RETRIES`                      | `1`                                                      |

Owner-supplied secrets:

| Key                   | Source                                                             |
| --------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL`        | Neon pooled connection string converted to SQLAlchemy asyncpg form |
| `DATABASE_DIRECT_URL` | Neon direct connection string converted to SQLAlchemy asyncpg form |
| `REDIS_URL`           | Upstash TLS Redis URL                                              |
| `LLM_BASE_URL`        | Hosted OpenAI-compatible provider base URL                         |
| `LLM_MODEL`           | Hosted LLaMA-compatible model name                                 |
| `LLM_API_KEY`         | Hosted provider API key                                            |

Generated secret:

| Key                      | Source                       |
| ------------------------ | ---------------------------- |
| `METRICS_INTERNAL_TOKEN` | Render `generateValue: true` |

Never print connection strings, tokens, or API keys in deploy logs or reports.

## Neon Setup

1. Create a Neon project on the Free plan.
2. Create a database named `groundstack`.
3. Copy both the pooled and direct connection strings with SSL required.
4. Convert the scheme from `postgresql://` to `postgresql+asyncpg://` for app variables.
5. Use the pooled URL for `DATABASE_URL`.
6. Use the direct URL for `DATABASE_DIRECT_URL`.

Run migrations as a one-off release task after Render has the database variables:

```bash
CONFIRM_PRODUCTION_MIGRATION=yes PYTHONPATH=apps/api python scripts/migrate_production.py
```

Verify pgvector after migrations:

```bash
PYTHONPATH=apps/api python scripts/db_smoke.py
```

## Upstash Setup

1. Create an Upstash Redis database on the Free plan.
2. Choose the closest free region to the Render API region.
3. Copy the TLS Redis URL for `REDIS_URL`.
4. Do not use REST credentials in this backend; GroundStack uses Redis protocol through
   `redis.asyncio`.

Verify connectivity through `/api/v1/health/ready` after Render deploys.

## LLM Provider Setup

Use a hosted provider that exposes an OpenAI-compatible `/v1/chat/completions` endpoint and a
LLaMA-compatible model. Configure:

- `LLM_PROVIDER=openai_compatible`
- `LLM_BASE_URL=https://<provider-host>/v1`
- `LLM_MODEL=<provider-model-name>`
- `LLM_API_KEY=<owner-entered-secret>`

Keep strict demo limits enabled. Do not run fine-tuning or upload adapters for this deployment.

## One-Off Release Tasks

Run only after the Render environment is configured:

```bash
make deploy-check
CONFIRM_PRODUCTION_MIGRATION=yes PYTHONPATH=apps/api python scripts/migrate_production.py
PYTHONPATH=apps/api python scripts/db_smoke.py
PYTHONPATH=apps/api python scripts/seed_demo.py
PYTHONPATH=apps/api python scripts/verify_demo_data.py
```

The seed command ingests only the fictional project demo corpus under
`apps/api/dev-data/knowledge-base`.

## Live Smoke Tests

After Vercel and Render are deployed:

```bash
curl -fsS https://groundstack-api.onrender.com/api/v1/health/live
curl -fsS https://groundstack-api.onrender.com/api/v1/health/ready
curl -fsS https://groundstack-api.onrender.com/api/v1/demo/availability
curl -fsS https://<vercel-project>.vercel.app
```

Manual browser checks:

- Landing page loads over HTTPS.
- Demo corpus is visible through user-safe UI paths.
- A grounded question returns citations.
- An unsupported question returns insufficient evidence.
- Prompt-injection content is not followed.
- Admin routes reject anonymous users.
- Rate limiting returns `429` after the configured threshold.
- Mobile layout and accessibility smoke checks pass.
- Client bundles, API responses, and logs do not expose secrets.

## Kill Switch

Set `DEMO_CHAT_ENABLED=false` in Render to put the public demo into maintenance mode. The
`/api/v1/demo/availability` endpoint should then report `maintenance`.
