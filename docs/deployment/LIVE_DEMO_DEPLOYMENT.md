# Hosted Deployment Preparation

No hosted deployment is created by this repository change. The checked-in manifests are
placeholders for a future owner-approved setup.

The simplified topology is:

- Next.js web app
- FastAPI API
- PostgreSQL with pgvector
- one OpenAI-compatible language-model provider

Before any hosted demonstration:

1. Create exact HTTPS frontend and API URLs.
2. Enter database, identity, and provider secrets directly in provider dashboards.
3. Set exact CORS and trusted-host values.
4. Run `alembic upgrade head` once against the intended database.
5. Upload only an approved neutral document through the protected interface.
6. Verify live, ready, supported, unsupported, citation, authorization, and secret-leak checks.

Do not treat the deployment as complete until a real provider request succeeds and every
citation is inspected. Do not upload private or customer material for a portfolio demo.
