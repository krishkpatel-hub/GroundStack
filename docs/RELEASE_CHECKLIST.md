# Release Checklist

Version: `1.0.0-rc.1`

## Preflight

- [x] `origin` points to `https://github.com/krishkpatel-hub/GroundStack.git`.
- [x] Milestone 11 Discord commits are merged into `origin/main`.
- [x] Milestone 12 benchmark commits are merged into `origin/main`.
- [x] Release branch `release/v1.0.0-rc1` created from latest `origin/main`.

## Required Before Final `v1.0.0`

- [ ] Owner chooses and adds a project license.
- [ ] Owner reviews release-candidate PR.
- [ ] Owner enables/validates GitHub security settings.
- [ ] Owner approves any production deployment, tag, or GitHub Release.
- [ ] Container image builds and a full Compose runtime smoke pass in an environment with Docker daemon access.
- [ ] Any skipped local checks are rerun in a suitable environment or documented as accepted risk.

## Evidence

- Claims registry: `docs/claims/CLAIMS.md`.
- Benchmark evidence: `docs/benchmarks/evidence/2026-08-23-smoke-dry-run.json`.
- Release audit: `docs/reports/FINAL_RELEASE_AUDIT.md`.
- Release manifest: `docs/RELEASE_MANIFEST_1.0.0_RC1.json`.
- Dependency inventory: `docs/reports/DEPENDENCY_LICENSE_INVENTORY.md`.
