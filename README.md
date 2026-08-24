# GroundStack

GroundStack is a portfolio-grade AI technical-support application for developer communities. It
answers questions from an admin-managed knowledge base using hybrid retrieval, reranking, grounded
generation, and citation validation. The `1.0.0-rc.1` branch packages the app as an audited,
reproducible release candidate with security notes, benchmark evidence, and interview-ready
documentation.

GroundStack does not claim production deployment, live Discord adoption, completed fine-tuning, real
usage volume, uptime, cost, or hosted-provider performance. Numeric claims are tracked in
`docs/claims/CLAIMS.md` and benchmark evidence is under `docs/benchmarks/`.

## What It Demonstrates

- Retrieval-augmented generation with pgvector, PostgreSQL full-text search, RRF fusion, reranking,
  and structured citations.
- Streaming grounded answers that are rejected when citations are missing, malformed, or fabricated.
- Admin source ingestion, evaluation records, feedback review, and training-candidate preparation.
- Discord slash-command integration that processes only explicit commands and keeps Discord data out
  of training.
- Release engineering: CI, migrations, Dockerfiles, deployment guardrails, reliability profiles,
  threat model, and evidence-backed claims.

## Prerequisites

- Node.js 22 or newer
- npm 10 or newer
- Python 3.12 or newer
- Docker Desktop or another Docker Compose-compatible runtime

## Setup

```bash
cp .env.example .env
make setup
make db-up
make migrate
```

## Run Locally

Run the full local stack:

```bash
make dev
```

Or run the API and web app in separate terminals:

```bash
make api-dev
make web-dev
```

The API runs at `http://localhost:8000` and the web app runs at `http://localhost:3000`.

For local answer generation, install Ollama and pull the configured model:

```bash
ollama pull llama3.2:3b
```

## Useful Commands

```bash
make setup      # install frontend and backend dependencies
make dev        # start database, apply migrations, and start the web app
make api-dev    # run FastAPI with reload
make web-dev    # run Next.js
make test       # run backend tests
make lint       # run backend lint, frontend lint, and frontend typecheck
make format     # format Python and TypeScript/CSS
make db-up      # start PostgreSQL with pgvector
make db-down    # stop local infrastructure
make migrate    # apply Alembic migrations
make ingest FILE=path/to/document.md
make ingest-sample
make eval-retrieval
make benchmark-retrieval
make validate-training-data
make prepare-training-data
make training-preflight
make train-qlora CONFIG=training/configs/smoke_test.yaml
make migration-check
make predeploy
```

## Architecture

- `apps/api` contains FastAPI routes, async SQLAlchemy wiring, ingestion services,
  parser/chunker/embedding boundaries, structured logging, tests, and Alembic migrations.
- `apps/web` contains the Next.js App Router shell, system-status indicator, and
  `/knowledge` page for file and URL ingestion.
- `docker-compose.yml` runs PostgreSQL with the `pgvector` extension.
- `docs` captures system architecture and delivery phases.

See [docs/architecture/SYSTEM_OVERVIEW.md](docs/architecture/SYSTEM_OVERVIEW.md),
[docs/architecture/RELEASE_INVENTORY.md](docs/architecture/RELEASE_INVENTORY.md),
[docs/architecture.md](docs/architecture.md), and [docs/ROADMAP.md](docs/ROADMAP.md).

## Environment

Configuration is loaded from environment variables. `.env.example` documents the local values and intentionally contains no secrets.

The frontend reads `NEXT_PUBLIC_API_BASE_URL` at build/runtime to contact the API from the browser.

`APP_ENV` must be one of `development`, `demo`, `production`, or `test`.
Production fails startup validation unless OIDC, exact CORS origins, trusted hosts,
secure cookies, and internal metrics-token settings are configured. Development can
enable `DEV_AUTH_BYPASS_ENABLED=true`; production cannot. Demo can allow anonymous
chat only when `ALLOW_ANONYMOUS_DEMO=true`, and anonymous actors remain quota-limited
and blocked from administrative routes.

OIDC settings include `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`,
`OIDC_AUDIENCE`, `OIDC_SCOPES`, `OIDC_ROLE_CLAIM`, `OIDC_ADMIN_ROLE`, and
`OIDC_ALLOWED_ALGORITHMS`.

Ingestion settings include `EMBEDDING_MODEL_NAME`, `EMBEDDING_DIMENSION`,
`EMBEDDING_BATCH_SIZE`, `CHUNK_TARGET_TOKENS`, `CHUNK_OVERLAP_TOKENS`,
`MAX_INGESTION_FILE_SIZE_BYTES`, and `URL_INGESTION_ALLOWED_DOMAINS`.

Retrieval settings include `VECTOR_CANDIDATE_LIMIT`, `LEXICAL_CANDIDATE_LIMIT`,
`RRF_K`, `RERANK_CANDIDATE_LIMIT`, `RETRIEVAL_FINAL_TOP_K`,
`MAX_CHUNKS_PER_SOURCE`, `RERANKER_MODEL_NAME`, `RERANKING_ENABLED`, and
`PERSIST_RETRIEVAL_QUERIES`.

Generation settings include `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`,
`LLM_API_KEY`, `LLM_TEMPERATURE`, `LLM_TOP_P`, `LLM_MAX_OUTPUT_TOKENS`,
`LLM_CONTEXT_WINDOW`, `LLM_REQUEST_TIMEOUT_SECONDS`, `LLM_PREWARM`,
`GENERATION_PROMPT_VERSION`, and `STORE_GENERATION_PROMPTS`. `LLM_PROVIDER=ollama`
is the default. `LLM_PROVIDER=openai_compatible` targets a `/v1/chat/completions`
compatible server.

## Knowledge Ingestion

Supported sources:

- Markdown: `.md`, `.markdown`
- Plain text: `.txt`
- HTML: `.html`, `.htm`
- Text-based PDF: `.pdf`
- One explicitly submitted public URL whose hostname is allowlisted

Pipeline stages:

```text
Source validation -> content extraction -> normalization -> metadata enrichment
-> structure-aware chunking -> embedding generation -> transactional persistence
-> ingestion report
```

Documents are immutable versions of a knowledge source. Re-ingesting unchanged
content reuses the existing version and marks the job as skipped. Changed content
for the same source creates the next document version. Chunks store heading path,
token count, checksum, `vector(384)` embedding, embedding model, metadata, and a
generated PostgreSQL text-search vector.

URL ingestion is intentionally strict: only HTTP/HTTPS, no embedded credentials,
allowlisted hostnames only, forbidden private or special IP ranges, no redirects,
strict timeouts, streamed response-size enforcement, supported content types only,
and no crawling.

FastAPI background tasks are used for this local milestone. They are process-local:
if the API process stops, in-flight work can stop with it. The orchestration boundary
is isolated so a durable worker queue can replace background tasks later.

## Retrieval

The retrieval API combines pgvector cosine search, PostgreSQL full-text search,
Reciprocal Rank Fusion, optional cross-encoder reranking, deterministic diversity
selection, and structured citations.

See [docs/retrieval.md](docs/retrieval.md).

## Grounded Generation

`POST /api/v1/chat/stream` streams conversation, retrieval, generation token, usage,
canonical answer, completion, and error events as Server-Sent Events. Answers are
generated only from retrieved source blocks, persisted with generation-run metadata,
and rejected when citations are missing, malformed, or fabricated. When no evidence
is found, GroundStack returns a deterministic insufficient-evidence answer without
calling the LLM.

See [docs/generation.md](docs/generation.md) and [docs/security.md](docs/security.md).

## Discord Community Assistant

GroundStack can expose the same grounded answer pipeline through Discord application
commands. It processes only explicit slash-command questions, avoids the Message
Content intent, disables DMs by default, encrypts temporary interaction tokens, and
marks Discord records as ineligible for training data.

Local inspection commands:

```bash
make discord-commands-json
make discord-worker-health
```

See [docs/discord.md](docs/discord.md) for sandbox setup, minimal permissions,
privacy, deletion, and deployment notes. The repository does not create or install a
Discord bot without explicit approval.

## Deployment

Production images live in `apps/api/Dockerfile` and `apps/web/Dockerfile`. The web
image uses Next.js standalone output; both images run as non-root users and include
health checks.

Single-host demo assets are under `deploy/`:

```bash
cp deploy/.env.demo.example deploy/.env.demo
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo build
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo run --rm api alembic upgrade head
docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo up -d
```

Only Caddy exposes public ports in the demo topology. PostgreSQL, Redis, API,
frontend, optional Ollama, and optional observability services are on internal
networks. Managed production can reuse the same containers with managed PostgreSQL
plus pgvector, managed Redis, an external OpenAI-compatible inference endpoint, and a
managed TLS/load-balancing layer.

Run `make migration-check` before applying migrations, then run migrations as a
separate one-off release task. Run `make predeploy` with the target environment
variables set before building or promoting a release.

Backups use `scripts/backup_postgres.sh`; restores use `scripts/restore_postgres.sh`.
Backups are timestamped, compressed, retention-pruned, and optionally encrypted with
`BACKUP_ENCRYPTION_KEY`.

## Product Screenshots

Deterministic Prompt 9 screenshots are stored in `docs/assets/screenshots/`:

- Landing page: `docs/assets/screenshots/landing.png`
- Chat with citations: `docs/assets/screenshots/chat-with-citations.png`
- Source viewer: `docs/assets/screenshots/source-viewer.png`
- Knowledge-base administration: `docs/assets/screenshots/knowledge-admin.png`
- Evaluation comparison: `docs/assets/screenshots/evaluation-comparison.png`
- Mobile chat: `docs/assets/screenshots/mobile-chat.png`

See `docs/CASE_STUDY.md` for a concise engineering case study.

## Public Demo Launch Preparation

GroundStack is prepared for a safe public demo architecture using Vercel for the
Next.js frontend, Render for the FastAPI API, Neon Postgres with pgvector, Upstash
Redis, and a user-supplied OpenAI-compatible hosted LLaMA endpoint. The repository
does not provision paid resources or store secrets.

Launch-readiness docs:

- Environment registry: `docs/deployment/ENVIRONMENT_VARIABLES.md`
- Platform setup: `docs/deployment/PLATFORM_SETUP.md`
- Launch runbook: `docs/deployment/LAUNCH_RUNBOOK.md`
- Demo corpus manifest: `docs/demo-corpus/MANIFEST.json`
- Claims evidence: `docs/claims/CLAIMS.md`
- Portfolio package: `docs/portfolio/`

Useful launch-prep commands:

```bash
make deploy-check
make migrate-production
make seed-demo
make verify-demo-data
make db-smoke
```

## Fine-Tuning Pipeline

`training/` contains an isolated dataset-engineering and QLoRA adapter-training
pipeline for GroundStack’s grounded support behavior. It includes a fictional
project-original seed dataset, provenance manifest, validation reports, deduplication,
leakage-resistant splits, TRL-style conversational formatting, hardware preflight,
tiny smoke training, adapter validation, deterministic evaluation helpers, model
manifest generation, and serving notes for PEFT/Transformers, vLLM, and Ollama.

The default configurable base model is `meta-llama/Llama-3.2-3B-Instruct`. You must
accept the Llama license and authenticate securely before any real training run.
Built with Llama.

See [docs/training.md](docs/training.md) and [training/README.md](training/README.md).

## Testing

```bash
make test
make lint
npm run test --workspace apps/web
python scripts/check_migrations.py
```

Backend endpoint tests use FastAPI's ASGI app directly and patch database or embedding
boundaries where needed. Production ingestion uses real Sentence Transformers embeddings.

Release-candidate evidence:

- Final audit: [docs/reports/FINAL_RELEASE_AUDIT.md](docs/reports/FINAL_RELEASE_AUDIT.md)
- Release checklist: [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)
- Known limitations: [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md)
- Threat model: [docs/security/THREAT_MODEL.md](docs/security/THREAT_MODEL.md)
- AI security review: [docs/security/AI_SECURITY_REVIEW.md](docs/security/AI_SECURITY_REVIEW.md)
- Capacity report: [docs/benchmarks/CAPACITY_REPORT.md](docs/benchmarks/CAPACITY_REPORT.md)

## Planned Phases

1. Feedback capture and answer-quality evaluation
2. Durable queueing for ingestion and generation jobs
3. LoRA/QLoRA supervised fine-tuning pipeline
4. Observability, load testing, and deployment hardening
