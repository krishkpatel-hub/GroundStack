# System Overview

GroundStack uses one browser application, one API, PostgreSQL with pgvector, a local embedding
model, and one OpenAI-compatible generation provider.

```text
Document
  -> FastAPI validation
  -> text extraction
  -> chunking
  -> embeddings
  -> PostgreSQL/pgvector

Question
  -> query embedding
  -> bounded pgvector similarity search
  -> relevance threshold
  -> evidence-only model prompt
  -> citation validation
  -> saved answer and conversation
```

## Boundaries

- `apps/web`: Next.js routes for overview, workspace, documents, history, health, and
  explanatory content.
- `apps/api/app/api/v1`: HTTP routes for auth, ingestion, documents, chat, conversations,
  feedback, and health.
- `apps/api/app/services/ingestion`: validation, extraction, chunking, embeddings, and
  transactional persistence.
- `apps/api/app/services/retrieval`: query validation, vector search, thresholding, and
  citation construction.
- `apps/api/app/services/generation`: evidence prompt construction, provider streaming,
  citation validation, and persistence.
- `apps/api/migrations`: reproducible PostgreSQL and pgvector schema history.

Document-management routes require an administrator principal. Chat and conversation routes
require an authorized user, except when the controlled single-instance demo mode is explicitly
enabled.
