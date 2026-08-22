# GroundStack Environment Variables

Values below are placeholders. Do not commit real secrets.

| Name | Service | Required environments | Secret | Example | Purpose | Validation | Rotation | Redeploy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `APP_ENV` | API | all | no | `demo` | Runtime safety mode | `development`, `demo`, `production`, or `test` | n/a | yes |
| `DATABASE_URL` | API | all | yes | `postgresql+asyncpg://...` | Application database connection | TLS required for managed demo | rotate DB password | yes |
| `DATABASE_DIRECT_URL` | API migration | hosted demo/prod | yes | `postgresql+asyncpg://...` | Direct migration connection for pooled providers | host/database displayed, credentials hidden | rotate DB password | no running app redeploy unless value changes |
| `DB_SSL_REQUIRED` | API | hosted demo/prod | no | `true` | Enforce TLS for Postgres | `true` for Neon/managed DB | n/a | yes |
| `DB_POOL_SIZE` | API | all | no | `5` | App-side DB connection cap | 1-20 | n/a | yes |
| `REDIS_URL` | API | public demo | yes | `rediss://...` | Rate limits, daily capacity, temporary demo state | `rediss://` for Upstash/managed Redis | rotate Redis token | yes |
| `REDIS_KEY_NAMESPACE` | API | all | no | `groundstack` | Key prefix for safe deletion | lowercase project namespace | n/a | yes |
| `DEMO_CHAT_ENABLED` | API | public demo | no | `true` | Public demo kill switch | `false` returns maintenance availability | n/a | yes |
| `DEMO_REDIS_REQUIRED` | API | public demo | no | `true` | Fail closed if Redis is unavailable | `true` for public hosted demo | n/a | yes |
| `DEMO_DAILY_QUESTION_LIMIT` | API | public demo | no | `100` | Global daily capacity | positive integer | n/a | yes |
| `DEMO_DAILY_TOKEN_LIMIT` | API | public demo | no | `15000` | Global approximate token ceiling | positive integer | n/a | yes |
| `DEMO_REQUEST_LIMIT_PER_MINUTE` | API | public demo | no | `8` | Per-client anonymous rate limit | 1-60 | n/a | yes |
| `DEMO_MAX_QUESTION_LENGTH` | API | public demo | no | `600` | Reject oversized questions | 20-2000 chars | n/a | yes |
| `LLM_PROVIDER` | API | all | no | `openai_compatible` | Generation provider | `ollama` locally, `openai_compatible` hosted | n/a | yes |
| `LLM_BASE_URL` | API | generation | secret-adjacent | `https://provider.example/v1-compatible` | Hosted inference endpoint | must expose `/v1/models` and chat completions | rotate if provider changes | yes |
| `LLM_API_KEY` | API | hosted generation | yes | `set-in-dashboard` | Hosted inference credential | never exposed to frontend | rotate provider key | yes |
| `LLM_MODEL` | API | generation | no | `llama-3.1-8b-instruct` | Exact model identifier | must be returned by provider model list | n/a | yes |
| `LLM_TIMEOUT_SECONDS` | API | hosted generation | no | `60` | Provider request timeout | positive seconds | n/a | yes |
| `LLM_MAX_OUTPUT_TOKENS` | API | generation | no | `500` | Maximum completion length | 1-4096 | n/a | yes |
| `LLM_MAX_CONCURRENT_REQUESTS` | API | public demo | no | `2` | Generation concurrency cap | 1-32 | n/a | yes |
| `CORS_ORIGINS` | API | all | no | `["https://app.example"]` | Approved frontend origins | exact origins only, no wildcard | n/a | yes |
| `TRUSTED_HOSTS` | API | all | no | `["api.example.com"]` | Host header allowlist | exact hosts only | n/a | yes |
| `DOCS_ENABLED` | API | dev only | no | `false` | API docs exposure | false in demo/prod | n/a | yes |
| `DEV_AUTH_BYPASS_ENABLED` | API | local dev only | no | `false` | Development auth bypass | false in demo/prod | n/a | yes |
| `NEXT_PUBLIC_API_BASE_URL` | Web | all | no | `https://api.example.com` | Browser-visible API base URL | never contains secrets | n/a | redeploy web |
| `DISCORD_INTEGRATION_ENABLED` | API, worker | Discord sandbox/prod | no | `false` | Enables signed Discord interactions only when credentials are present | startup validation requires all Discord secrets when true | n/a | yes |
| `DISCORD_APPLICATION_ID` | API, worker | Discord sandbox/prod | secret-adjacent | `set-in-dashboard` | Discord application/client ID for interactions and webhook followups | numeric Discord snowflake | rotate app if compromised | yes |
| `DISCORD_PUBLIC_KEY` | API | Discord sandbox/prod | no | `set-in-dashboard` | Ed25519 public key for request signature verification | hex public key from Discord app | rotate in Discord portal | yes |
| `DISCORD_BOT_TOKEN` | API, worker | Discord sandbox/prod | yes | `set-in-dashboard` | Bot token for future command registration and moderator-channel delivery | never exposed to frontend or logs | rotate immediately if exposed | yes |
| `DISCORD_INTERACTION_TOKEN_ENCRYPTION_KEY` | API, worker | Discord sandbox/prod | yes | `set-in-dashboard` | Encrypts temporary interaction tokens while queued | Fernet key or high-entropy secret | rotate with queue drain | yes |
| `DISCORD_IDENTITY_HMAC_KEY` | API, worker | Discord sandbox/prod | yes | `set-in-dashboard` | Creates privacy-preserving Discord user identifiers | high-entropy secret | rotate with documented ownership impact | yes |
| `DISCORD_DEFAULT_RETENTION_DAYS` | API | Discord sandbox/prod | no | `30` | Default retention for controls and guild config | 1-365 | n/a | yes |
| `DISCORD_ALLOW_DMS` | API | Discord sandbox/prod | no | `false` | Allows direct-message use when explicitly enabled | false by default | n/a | yes |

Changing secret values in Render, Vercel, Neon, Upstash, or the inference provider should be followed
by a redeploy or service restart where that platform requires it.
