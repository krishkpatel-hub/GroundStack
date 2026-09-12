# Environment Variables

The complete safe template is [.env.example](../../.env.example). Required local groups are:

- Application: `APP_ENV`, `PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_API_BASE_URL`,
  `CORS_ORIGINS`, `TRUSTED_HOSTS`.
- Database: `DATABASE_URL` and optional `DATABASE_DIRECT_URL`.
- Embeddings: `EMBEDDING_MODEL_NAME`, `EMBEDDING_DIMENSION`.
- Retrieval: `RETRIEVAL_CANDIDATE_LIMIT`, `RETRIEVAL_MAX_TOP_K`,
  `RETRIEVAL_MAX_VECTOR_DISTANCE`.
- Generation: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, and, for a hosted
  provider, `LLM_API_KEY`.

`NEXT_PUBLIC_API_BASE_URL` is the only browser-visible runtime value and must never contain
a secret. `DATABASE_URL`, `OIDC_CLIENT_SECRET`, and `LLM_API_KEY` are server-only.

Development may use `DEV_AUTH_BYPASS_ENABLED=true` only with
`APP_ENV=development`. Hosted production configuration rejects that combination.
