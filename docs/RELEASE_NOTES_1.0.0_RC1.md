# GroundStack 1.0.0-rc.1 Release Notes

GroundStack `1.0.0-rc.1` is a reviewable release candidate for a portfolio-grade AI
technical-support application. It freezes feature scope and focuses on reproducibility, security
review, evidence, and recruiter-ready documentation.

## Included

- Knowledge ingestion, hybrid retrieval, reranking, grounded generation, citation validation, and
  conversation persistence.
- Feedback, deterministic evaluation, and human-reviewed training-candidate workflow.
- Offline fine-tuning data preparation and QLoRA workflow scaffolding.
- Discord slash-command adapter with privacy boundaries and mock-tested backend flows.
- Load/reliability harness with synthetic profiles and claims registry.
- Deployment, security, operations, release, and portfolio documentation.

## Evidence

- Backend tests, frontend tests/build, Playwright e2e/accessibility tests, load-harness unit tests,
  migration checks, dependency scans, and local dry-run benchmark evidence are recorded in the final
  audit.
- No production traffic, live Discord usage, hosted-provider capacity, or real fine-tuning result is
  claimed.

## Release Boundaries

This branch does not create a final tag, publish a GitHub Release, merge to `main`, deploy
production infrastructure, or provision paid services.
