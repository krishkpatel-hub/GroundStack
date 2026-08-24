# Dependency and License Inventory

Date: 2026-08-23  
Version: `1.0.0-rc.1`

This inventory is a release-candidate evidence snapshot, not a formal legal review.

## JavaScript Workspace

Command:

```bash
npm ls --workspaces --depth=0
```

Top-level workspace packages:

| Package | Version |
| --- | --- |
| `@groundstack/web` | `1.0.0-rc.1` |
| `@axe-core/playwright` | `4.13.0` |
| `@playwright/test` | `1.62.1` |
| `@tailwindcss/postcss` | `4.3.3` |
| `eslint` | `9.39.5` |
| `eslint-config-next` | `16.3.1` |
| `lucide-react` | `0.539.0` |
| `next` | `16.3.1` |
| `react` | `19.2.8` |
| `react-dom` | `19.2.8` |
| `react-markdown` | `10.1.0` |
| `remark-gfm` | `4.0.1` |
| `tailwindcss` | `4.3.3` |
| `typescript` | `5.9.3` |
| `vitest` | `4.1.11` |

Audit command:

```bash
npm audit --audit-level=high
```

Result: `0` known high-or-higher vulnerabilities reported.

## Python Environment

Command:

```bash
cd apps/api
. .venv/bin/activate
python -m pip list --format=freeze
```

Primary runtime and evaluation packages present in the release environment include:

| Package | Version |
| --- | --- |
| `fastapi` | `0.141.1` |
| `uvicorn` | `0.52.3` |
| `SQLAlchemy` | `2.0.52` |
| `alembic` | `1.19.1` |
| `asyncpg` | `0.31.0` |
| `Authlib` | `1.7.2` |
| `cryptography` | `50.0.0` |
| `httpx` | `0.28.1` |
| `pydantic` | `2.13.4` |
| `pydantic-settings` | `2.15.0` |
| `redis` | `8.1.0` |
| `pytest` | `9.1.1` |
| `ruff` | `0.16.3` |
| `locust` | `2.46.3` |
| `sentence-transformers` | `6.0.0` |
| `transformers` | `5.15.0` |
| `torch` | `2.13.0` |

Audit command:

```bash
cd apps/api
. .venv/bin/activate
python -m pip_audit --path .
```

Result: no known vulnerabilities reported. The local editable first-party package was skipped by
`pip-audit` because it is not a PyPI package.

## SBOM Status

No committed CycloneDX or SPDX SBOM is included in `1.0.0-rc.1`. Generating and signing a complete
SBOM is a release gate before a final `v1.0.0` tag.
