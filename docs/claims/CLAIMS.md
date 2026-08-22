# Claims Evidence Report

| Claim | Measurement method | Dataset | Environment | Date | Result | Reproduction command | Evidence artifact | Suitable for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API test suite passed | pytest | repository tests | local development | 2026-08-20 | 36 passed, 1 skipped | `cd apps/api && pytest` | terminal run from Milestone 9 | README/interview |
| Web E2E/accessibility suite passed | Playwright with mocked API and axe scan | deterministic test fixtures | local development | 2026-08-20 | 28 passed | `npm run test:e2e --workspace apps/web` | Playwright output and screenshots | README/interview |
| Static web assets stayed under budget | Next production build asset walk | built `.next/static` | local development | 2026-08-20 | 1,175,514 bytes across 33 assets | `npm run perf:check --workspace apps/web` | perf-check output | README/interview |
| Production-like Docker Compose smoke passed | Compose health checks plus Caddy HTTP smoke | seeded local demo config | local Docker | 2026-08-20 | API, web, Redis, Postgres, Caddy healthy; HTTP 200 via Caddy | `docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo up -d --build --wait` | Compose status and curl output | interview |

Do not promote unmeasured claims such as public usage, production adoption, accuracy improvements,
or latency reductions.
