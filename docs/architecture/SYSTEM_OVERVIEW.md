# GroundStack System Overview

Version: `1.0.0-rc.1`

GroundStack is a local-first AI technical-support application for answering questions from an
admin-managed knowledge base. It combines document ingestion, hybrid retrieval, reranking,
grounded generation, citation validation, feedback review, evaluation, training-data preparation,
Discord slash-command integration, and release evidence.

## Components

- `apps/web`: Next.js App Router frontend for asking questions, inspecting citations, viewing
  conversations, managing knowledge ingestion, evaluation, training candidates, settings, and
  Discord escalation/configuration.
- `apps/api`: FastAPI backend with OIDC/demo auth, ingestion, retrieval, chat, feedback,
  evaluation, training-candidate, metrics, Discord, and health routes.
- `apps/api/migrations`: Alembic schema history through `202608220001`.
- `training`: offline dataset validation, splitting, QLoRA configuration, adapter validation, and
  serving utilities. No completed real fine-tuning run is claimed.
- `evaluation`: deterministic regression cases and evaluation runners.
- `load`: deterministic Locust profiles, synthetic datasets, response assertions, and benchmark
  manifest generation.
- `deploy`: single-host demo Compose topology with Caddy, API, web, Postgres, Redis, optional
  Ollama, and optional observability.
- `render.yaml`: preview/demo deployment outline for API and Discord worker; it does not provision
  resources from this repository.

## Request Flow

1. Admins ingest Markdown, text, HTML, text-based PDFs, or allowlisted URLs.
2. The API parses, normalizes, chunks, embeds, and persists immutable document versions.
3. User questions create scoped conversations and run hybrid retrieval.
4. Retrieval combines pgvector vector search, PostgreSQL full-text search, reciprocal-rank fusion,
   optional cross-encoder reranking, diversity selection, and structured citations.
5. Grounded generation uses Ollama, an OpenAI-compatible provider, or the deterministic fake
   provider for tests/benchmarks.
6. Citation validation rejects fabricated or unsupported citations. Empty evidence returns a
   deterministic insufficient-evidence answer without calling the LLM.
7. Feedback can create training candidates, but human approval is required before export.

## Discord Flow

Discord support is an adapter over the same RAG path. It accepts signed application-command
interactions at `/integrations/discord/interactions`, verifies Ed25519 signatures, deduplicates
interactions, queues encrypted jobs, and renders Discord-safe answers with mentions disabled.
GroundStack does not scan ordinary Discord messages, does not require Message Content intent, and
marks Discord data as `training_eligible=false`.

## Deployment Status

The repository contains local, demo, and managed-platform configuration. No production deployment,
GitHub Release, or public Discord installation is claimed for `1.0.0-rc.1`.
