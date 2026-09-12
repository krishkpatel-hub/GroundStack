# Changelog

## 1.0.0-rc.1 - 2026-08-23

### Added

- Admin-managed knowledge ingestion for Markdown, text, HTML, text-based PDFs, and allowlisted URLs.
- Semantic vector retrieval with pgvector, an explicit relevance threshold, and structured citations.
- Grounded streaming answers with citation validation, repair, and deterministic insufficient
  evidence behavior.
- Conversation feedback, persistence, health checks, backup/restore scripts, OIDC/demo auth, and CI.

### Changed

- Prepared API and web package metadata for release candidate `1.0.0-rc.1`.
- Reduced the presentation build to the web app, FastAPI, PostgreSQL/pgvector, and one hosted
  OpenAI-compatible provider.
- Reorganized architecture, security, operations, and presentation documentation.

### Not Included

- No final `v1.0.0` tag or GitHub Release.
- No production deployment.
