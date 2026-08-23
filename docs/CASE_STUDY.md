# GroundStack Case Study

## Problem

Developer communities need support answers that are useful without drifting away from the available
documentation. GroundStack explores a portfolio-grade pattern for grounded AI support: ingest
technical sources, retrieve evidence, stream an answer, validate citations, and capture feedback for
reviewed improvement.

## Users

- Anonymous demo visitors who can ask quota-limited questions.
- Signed-in users who keep their own conversations and feedback.
- Administrators who manage sources, evaluation, training candidates, and deployment settings.

## Product Goals

- Make the first question fast to ask.
- Keep citations inspectable and separate from generated text.
- Show uncertainty clearly when evidence is missing or services are unavailable.
- Keep admin workflows dense, auditable, and reversible where possible.

## Architecture

GroundStack uses Next.js for the web product and FastAPI for the API. PostgreSQL with pgvector stores
documents, chunks, conversations, feedback, evaluation records, and training candidates. Redis is
available for deployment topology support. Caddy fronts the single-host demo stack.

## Retrieval Pipeline

Sources are parsed, normalized, chunked, embedded, and versioned. Retrieval combines vector search,
PostgreSQL full-text search, reciprocal rank fusion, optional reranking, and diversity selection.
Citation validation rejects unsupported or fabricated citation IDs before an answer is treated as
grounded.

## Model Strategy

The default local path targets Ollama with a LLaMA-family model. The API also supports an
OpenAI-compatible endpoint. Test mode uses fake/local providers unless explicitly overridden.

## Safety Decisions

Production requires OIDC configuration, exact CORS origins, trusted hosts, secure cookies, and an
internal metrics token. Anonymous demo users cannot mutate knowledge, run evaluations, review
training, or change settings. Feedback can create training candidates, but those candidates require
human review before export.

The Discord adapter uses signed slash-command interactions rather than message scanning. It encrypts
temporary interaction tokens, suppresses mentions in generated output, uses keyed HMAC user
identifiers, disables DMs by default, and marks Discord records as ineligible for training data.

## Evaluation Approach

The repository includes deterministic regression datasets, evaluation runners, persisted evaluation
records, and a UI for comparing runs by dataset, prompt version, retrieval configuration, model
metadata, pass rate, and report path.

## Production Architecture

The single-host demo uses Caddy, Next.js, FastAPI, PostgreSQL with pgvector, Redis, optional Ollama,
and optional Prometheus on internal Docker networks. Managed production can reuse the same images
with managed PostgreSQL, managed Redis, external inference, and a managed TLS/load-balancing layer.

## Tradeoffs

- The knowledge base is shared and admin-managed, not a tenant-isolated corpus.
- Sessions use HttpOnly cookies around provider tokens rather than a server-side session store.
- Demo seeding uses deterministic synthetic/project-authored content rather than fake production
  activity.
- The backend remains the authority for authorization; role-aware navigation is a usability layer.
- The Discord milestone implements local code, mocks, documentation, and admin controls; it does not
  claim a production bot installation or public community usage.

## Measured

- Backend tests, frontend unit tests, production builds, deterministic evaluation runs, Compose
  rendering, predeploy checks, and production Docker builds were executed during Milestones 8 and 9.
- Prompt 9 adds repeatable Playwright journeys, axe scans, and a frontend static asset budget check.
- Milestone 11 adds Discord-specific unit tests for signature verification, command parsing,
  answer rendering, mention suppression, and training-data exclusion.

## Future Work

- Server-side session store and provider revocation integration.
- Durable ingestion/generation workers.
- Tenant-isolated knowledge workspaces.
- Richer trend analysis across evaluation runs.
- Full manual assistive-technology review with a real screen reader.
