# Changelog

## 1.0.0-rc.1 - 2026-08-23

### Added

- Admin-managed knowledge ingestion for Markdown, text, HTML, text-based PDFs, and allowlisted URLs.
- Hybrid retrieval with pgvector, PostgreSQL full-text search, RRF fusion, reranking, diagnostics,
  and structured citations.
- Grounded streaming answers with citation validation, repair, and deterministic insufficient
  evidence behavior.
- Feedback, evaluation records, and human-reviewed training-candidate workflow.
- Offline fine-tuning data preparation and QLoRA workflow scaffolding.
- Discord slash-command integration with signed interactions, encrypted queued jobs, feedback, data
  deletion, and admin escalation review.
- Reliability/load-test harness, cost estimator, claims registry, and release evidence docs.
- Demo/deployment guardrails, OIDC/demo auth, metrics, health checks, backup/restore scripts, and CI.

### Changed

- Prepared API and web package metadata for release candidate `1.0.0-rc.1`.
- Reorganized final architecture, security, operations, and portfolio documentation.

### Not Included

- No final `v1.0.0` tag or GitHub Release.
- No production deployment.
- No public Discord installation.
- No completed real fine-tuning run.
