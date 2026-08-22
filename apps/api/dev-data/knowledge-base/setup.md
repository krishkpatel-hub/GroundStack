# GroundStack Local Setup

GroundStack runs with a FastAPI API, a Next.js console, and PostgreSQL with pgvector.

## Environment

Copy `.env.example` to `.env`, then confirm the database URL points at the local
PostgreSQL service.

```bash
cp .env.example .env
make db-up
make migrate
```

## Common Checks

- The API health endpoint should return `status: ok`.
- The system status endpoint should show the database as connected.
- The web console reads the API base URL from `NEXT_PUBLIC_API_BASE_URL`.
- The Knowledge Base page should list only documents returned by the API.
- Re-ingesting changed source content creates a new immutable document version.
- Chunk previews should preserve list items without duplicating them.
