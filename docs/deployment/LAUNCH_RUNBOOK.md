# Public Demo Launch Runbook

This runbook prepares a public demo without provisioning paid resources from code.

## Checkpoint A: Repository Readiness

1. Confirm `main` is pushed to `https://github.com/krishkpatel-hub/GroundStack`.
2. Work from `launch/public-demo`.
3. Run `make test`, `make lint`, `make typecheck`, `make predeploy`, and `make deploy-check`.
4. Run the secret scan described in the release checklist before pushing.

## Checkpoint B: Infrastructure Configuration

Create only free or explicitly approved resources:

- Neon Postgres with pgvector enabled.
- Upstash Redis using TLS.
- Render web service for `apps/api/Dockerfile`.
- Vercel project for `apps/web`.
- OpenAI-compatible hosted LLaMA inference endpoint supplied by the user.
- Optional Discord application credentials only after explicit owner approval.

Do not paste secrets into repository files. Set them in provider dashboards.

## Checkpoint C: Backend Launch

1. Set Render environment variables from `ENVIRONMENT_VARIABLES.md`.
2. Keep `DEMO_CHAT_ENABLED=false` until checks pass.
3. Run `make migrate-production` with `CONFIRM_PRODUCTION_MIGRATION=yes`.
4. Run `make db-smoke`.
5. Run `make seed-demo` and `make verify-demo-data`.
6. Verify `/api/v1/health/live`, `/api/v1/health/ready`, and `/api/v1/demo/availability`.
7. Turn on `DEMO_CHAT_ENABLED=true`.

## Optional Discord Sandbox

1. Keep `DISCORD_INTEGRATION_ENABLED=false` until the public API endpoint is reachable.
2. Set Discord secrets only in the deployment dashboard.
3. Verify the interaction endpoint with Discord's PING challenge.
4. Run `make discord-commands-json` locally and review the minimal scopes.
5. Register guild-scoped commands in a private development server using the reviewed payload.
6. Start the private Discord worker service.
7. Enable one test guild and one allowed channel from `/discord` in the admin UI.
8. Test `/ask`, feedback, escalation, and `/delete-my-data`.

Do not create a public bot listing, install into external servers, or enable production
Discord use without explicit approval.

## Checkpoint D: Frontend Launch

1. Configure Vercel with `NEXT_PUBLIC_API_BASE_URL` pointing to the Render API URL.
2. Build with `npm run build --workspace apps/web`.
3. Verify streaming, citations, mobile layout, and error states.

## Checkpoint E: Public Verification

Run safe live checks only:

- `.env`, `.git`, API docs, admin routes, uploads, ingestion, metrics, and training endpoints are inaccessible.
- CORS rejects an unapproved origin.
- Rate limits and oversized request handling return honest errors.
- Prompt injection in demo corpus does not override instructions.

## Operations

- Shutdown: set `DEMO_CHAT_ENABLED=false`, then suspend frontend/backend services if needed.
- Cost spike: lower `DEMO_DAILY_QUESTION_LIMIT`, lower `LLM_MAX_OUTPUT_TOKENS`, or set the kill switch.
- Redis key cleanup: delete keys matching `groundstack:demo:demo:*`.
- Demo data removal: run a reviewed SQL deletion scoped to demo sources only; do not truncate shared tables.
- Rollback: redeploy the previous Render/Vercel build and keep migrations forward-only unless a backup restore is approved.
