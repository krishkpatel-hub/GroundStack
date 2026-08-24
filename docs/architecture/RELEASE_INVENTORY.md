# Release Inventory

Version: `1.0.0-rc.1`

## Applications And Packages

| Path | Role | Release status |
| --- | --- | --- |
| `apps/web` | Next.js product/admin UI | Included |
| `apps/api` | FastAPI API, workers, CLI utilities | Included |
| `training` | Offline training-data and QLoRA workflow | Included as reproducible workflow |
| `evaluation` | Deterministic evaluation package | Included |
| `load` | Synthetic load and reliability harness | Included |
| `deploy` | Single-host demo deployment assets | Included, not deployed by this release |

## API Surface

- `/api/v1/auth/*`: OIDC/demo identity endpoints.
- `/api/v1/chat` and `/api/v1/chat/stream`: grounded answer generation.
- `/api/v1/conversations/*`: scoped conversation history.
- `/api/v1/documents/*` and `/api/v1/ingestions/*`: admin knowledge ingestion and inspection.
- `/api/v1/retrieval/*`: retrieval configuration, search, and run inspection.
- `/api/v1/messages/*/feedback`: answer feedback.
- `/api/v1/evaluation/*`: admin evaluation records.
- `/api/v1/training/*`: admin training-candidate review.
- `/api/v1/discord/*`: admin Discord configuration and escalations.
- `/api/v1/health`, `/api/v1/health/live`, `/api/v1/health/ready`, `/api/v1/system/status`,
  `/api/v1/demo/availability`, `/api/v1/metrics`.
- `/integrations/discord/interactions`: signed Discord application-command endpoint.

## Data Stores

- PostgreSQL with pgvector stores sources, document versions, chunks, conversations, generation
  runs, retrieval runs, feedback, evaluation records, training candidates, and Discord records.
- Redis is optional locally and expected for public demo rate limits/replay protection.
- The filesystem stores prompts, docs, deterministic seed/evaluation data, and ignored local
  reports/caches.

## Migrations

Current Alembic head: `202608220001`. Fresh-database migration is part of the verification matrix.

## Providers

- Embeddings and reranking: sentence-transformers by default.
- Generation: Ollama, OpenAI-compatible endpoint, and deterministic fake provider for tests/load.
- No paid provider call is made by default.

## Evidence

- Claims registry: `docs/claims/CLAIMS.md`.
- Benchmark dry-run evidence: `docs/benchmarks/evidence/2026-08-23-smoke-dry-run.json`.
- Evaluation reports: `evaluation/reports/`.
- Prompt/version metadata: `apps/api/app/prompts/grounded_answer/v1/metadata.json`.
