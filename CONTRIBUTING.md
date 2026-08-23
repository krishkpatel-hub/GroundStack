# Contributing

GroundStack `1.0.0-rc.1` is in scope freeze. Pull requests should be small and release-focused.

## Allowed During RC

- Release-blocking correctness fixes.
- Security, privacy, accessibility, and test repairs.
- Documentation corrections that make claims more accurate.
- Reproducibility fixes for setup, verification, or release evidence.

## Avoid During RC

- New product features, providers, integrations, major refactors, framework migrations, or UI
  redesigns.
- Paid service calls, production deployments, final tags, or GitHub Releases without owner approval.
- Fabricated screenshots, metrics, usage, or benchmark claims.

## Verification

Run the relevant subset for your change:

```bash
make lint
make typecheck
make test
npm run build --workspace apps/web
python scripts/check_migrations.py
PYTHONPATH=. python -m pytest tests/load
```

For release-candidate changes, record skipped checks and why. Do not describe skipped tests as
passed.

## Data Safety

Do not commit `.env` files, credentials, private datasets, uploaded documents, generated reports,
local databases, model weights, adapters, caches, logs, or production screenshots containing secrets.
