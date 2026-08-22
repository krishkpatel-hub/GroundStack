# Platform Setup Notes

## Neon

- Use a Postgres version that supports pgvector.
- Enable `vector` with `CREATE EXTENSION IF NOT EXISTS vector;`.
- Use pooled `DATABASE_URL` for the running app and direct `DATABASE_DIRECT_URL` for migrations.
- Set `DB_SSL_REQUIRED=true`.

## Upstash

- Use the provider's TLS Redis URL, usually `rediss://...`.
- Set `DEMO_REDIS_REQUIRED=true` for the public demo.
- GroundStack keys are namespaced by `REDIS_KEY_NAMESPACE`, `APP_ENV`, and `demo`.

## Render

- Use `render.yaml` as a blueprint reference.
- Keep auto-deploy disabled until the launch branch is verified.
- Health check: `/api/v1/health/live`.
- Readiness check: `/api/v1/health/ready`.
- Do not run migrations automatically from multiple replicas.

## Vercel

- Import `krishkpatel-hub/GroundStack`.
- Root directory: `apps/web`.
- Build command: `npm run build`.
- Set `NEXT_PUBLIC_API_BASE_URL` to the exact Render backend URL.
- Configure production and preview environments separately. Do not wildcard preview origins in API CORS.

## Hosted LLaMA Endpoint

The API expects an OpenAI-compatible service:

- `GET /v1/models` returns the exact `LLM_MODEL`.
- `POST /v1/chat/completions` supports streaming.
- The key is stored only as `LLM_API_KEY` in backend hosting.
