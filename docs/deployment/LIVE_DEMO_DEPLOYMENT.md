# Live Demo Deployment Runbook

This runbook deploys the simplified GroundStack demo with Vercel, Render, Neon
PostgreSQL with pgvector, and one owner-approved OpenAI-compatible LLaMA provider.
It uses only the fictional Northstar Systems corpus. Do not enter secrets into source
control, GitHub issues, PR comments, or chat.

## Current Gate

The complete local user-acceptance test passed on the `review/product-hardening`
line and those fixes are included in `deploy/simplified-live-demo`. Live deployment
still requires owner access to Vercel, Render, Neon, and the selected inference
provider. No authenticated deployment CLI or connector is configured in this
workspace, so Codex can prepare manifests and verification commands but cannot
create hosted services or enter private secrets.

## Actions Codex Can Perform

1. Keep deployment files aligned with the simplified architecture.
2. Build and test the web and API locally.
3. Verify the Northstar demo seed and reset commands against the local database.
4. Push the deployment branch and provide a pull-request URL.
5. Run live smoke tests after the owner supplies the public frontend and backend URLs.

## Browser Or Account Actions For The Owner

1. Vercel: import `krishkpatel-hub/GroundStack`, select the free Hobby option,
   set the project root to `apps/web`, and use the deployment branch until the PR
   is merged.
2. Render: create a free Docker web service from this repository using
   `render.yaml`; keep auto-deploy off until CI and smoke tests pass.
3. Neon: create a free PostgreSQL project, create a `groundstack` database, and
   enable `pgvector`.
4. LLM provider: choose an already-approved hosted OpenAI-compatible LLaMA
   endpoint and create the API key inside that provider dashboard.
5. Run the one-off migration and seed commands from a local checkout with private
   environment variables set outside the repository. Render free web services do
   not provide an interactive one-off shell.
6. Enter private secrets only in provider dashboards or an untracked local shell
   session. Never paste connection
   strings, API keys, passwords, or tokens into chat.

Stop before selecting any paid tier, adding a card where it is not required,
enabling paid autoscaling, or increasing quotas beyond the free tier.

## Public Non-Secret Configuration

### Vercel

| Field | Value |
| --- | --- |
| Project name | `groundstack-demo` |
| Framework preset | Next.js |
| Root directory | `apps/web` |
| Install command | `cd ../.. && npm ci` |
| Build command | `cd ../.. && npm run build --workspace apps/web` |
| Output directory | `.next` |
| Production branch | `main` after the deployment PR is merged |
| Preview branch | `deploy/simplified-live-demo` before merge |
| `NEXT_PUBLIC_API_BASE_URL` | `https://groundstack-api.onrender.com` |
| `NEXT_PUBLIC_SITE_URL` | `https://<vercel-project>.vercel.app` |

### Render

`render.yaml` defines one API web service. It intentionally does not deploy
Redis, Discord workers, training workers, rerank workers, or observability sidecars.

| Key | Value |
| --- | --- |
| `APP_ENV` | `demo` |
| `ALLOW_ANONYMOUS_DEMO` | `true` |
| `DEV_AUTH_BYPASS_ENABLED` | `false` |
| `DOCS_ENABLED` | `false` |
| `DEMO_CHAT_ENABLED` | `true` |
| `DEMO_REDIS_REQUIRED` | `false` |
| `DEMO_REQUEST_LIMIT_PER_MINUTE` | `4` |
| `DEMO_DAILY_QUESTION_LIMIT` | `40` |
| `DEMO_DAILY_TOKEN_LIMIT` | `10000` |
| `DEMO_MAX_QUESTION_LENGTH` | `500` |
| `DEMO_MAX_CONTEXT_TOKENS` | `2200` |
| `DEMO_PROVIDER_FAILURE_THRESHOLD` | `3` |
| `DEMO_PROVIDER_FAILURE_WINDOW_SECONDS` | `300` |
| `DEMO_UPLOAD_LIMIT_BYTES` | `0` |
| `DEMO_MAX_CONVERSATIONS` | `3` |
| `DB_SSL_REQUIRED` | `true` |
| `LLM_PROVIDER` | `openai_compatible` |
| `LLM_TIMEOUT_SECONDS` | `45` |
| `LLM_REQUEST_TIMEOUT_SECONDS` | `45` |
| `LLM_MAX_OUTPUT_TOKENS` | `500` |
| `LLM_MAX_CONCURRENT_REQUESTS` | `2` |
| `LLM_MAX_RETRIES` | `1` |
| `DISCORD_INTEGRATION_ENABLED` | `false` |
| `DISCORD_ALLOW_DMS` | `false` |

Set these after the hosted URLs are known:

| Key | Value |
| --- | --- |
| `CORS_ORIGINS` | `https://<vercel-project>.vercel.app` |
| `TRUSTED_HOSTS` | `groundstack-api.onrender.com,<custom-api-host-if-used>` |
| `PUBLIC_API_BASE_URL` | `https://groundstack-api.onrender.com` |

## Private Secrets The Owner Enters Directly

| Key | Dashboard | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Render | Neon pooled URL converted to `postgresql+asyncpg://...` |
| `DATABASE_DIRECT_URL` | Render | Neon direct URL converted to `postgresql+asyncpg://...` |
| `LLM_BASE_URL` | Render | Hosted provider base URL ending in `/v1` if required by provider |
| `LLM_MODEL` | Render | Exact hosted LLaMA-compatible model identifier |
| `LLM_API_KEY` | Render | Hosted provider API key |
| `METRICS_INTERNAL_TOKEN` | Render | Use Render `generateValue` from `render.yaml` |

No private secrets are required in Vercel for the current frontend.

## Neon Setup

1. Create a Neon project on the free plan.
2. Create a database named `groundstack`.
3. Enable pgvector with `CREATE EXTENSION IF NOT EXISTS vector;`.
4. Copy both pooled and direct connection strings with SSL required.
5. Convert the scheme from `postgresql://` to `postgresql+asyncpg://`.
6. Use the pooled URL for `DATABASE_URL`.
7. Use the direct URL for `DATABASE_DIRECT_URL`.

## One-Off Release Tasks

Run only after Neon is created and the provider variables are known. On the free
target stack, run these from a local checkout or another owner-controlled
one-off environment with private variables set outside source control. Do not
print secret values.

```bash
PYTHONPATH=apps/api python scripts/deploy_check.py
CONFIRM_PRODUCTION_MIGRATION=yes PYTHONPATH=apps/api python scripts/migrate_production.py
PYTHONPATH=apps/api python scripts/db_smoke.py
PYTHONPATH=apps/api python scripts/seed_demo.py
PYTHONPATH=apps/api python scripts/verify_demo_data.py
```

`scripts/seed_demo.py` ingests only the fictional Northstar Systems corpus under
`docs/demo-corpus/northstar`. Running it again reuses unchanged document versions;
use `scripts/seed_demo.py --reset` only for an intentional demo reset.

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
- Documents are available through the fictional Northstar demo workspace.
- A supported question returns an evidence-grounded answer with citations.
- Citation excerpts match the source documents.
- An unsupported question returns insufficient evidence instead of general knowledge.
- Conversation history saves and reloads.
- Protected document-administration routes reject anonymous users.
- Mobile layout works at 320, 375, 768, 1024, and 1440 pixel widths.
- Client bundles, requests, responses, and logs do not expose secrets.

## Kill Switch And Limits

Set `DEMO_CHAT_ENABLED=false` in Render to put the public demo into maintenance
mode. Keep `DEMO_UPLOAD_LIMIT_BYTES=0` so anonymous users cannot upload documents.
The simplified deployment uses one Render API instance and in-process demo
throttles. Those limits protect the free demo instance but reset on restart and
are not cross-instance distributed.
