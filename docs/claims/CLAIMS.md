# Claims Evidence Report

| Claim | Measurement method | Dataset | Environment | Date | Result | Reproduction command | Evidence artifact | Suitable for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API test suite passed | pytest | repository tests | local development | 2026-08-20 | 36 passed, 1 skipped | `cd apps/api && pytest` | terminal run from Milestone 9 | README/interview |
| Web E2E/accessibility suite passed | Playwright with mocked API and axe scan | deterministic test fixtures | local development | 2026-08-20 | 28 passed | `npm run test:e2e --workspace apps/web` | Playwright output and screenshots | README/interview |
| Static web assets stayed under budget | Next production build asset walk | built `.next/static` | local development | 2026-08-20 | 1,175,514 bytes across 33 assets | `npm run perf:check --workspace apps/web` | perf-check output | README/interview |
| Production-like Docker Compose smoke passed | Compose health checks plus Caddy HTTP smoke | seeded local demo config | local Docker | 2026-08-20 | API, web, Redis, Postgres, Caddy healthy; HTTP 200 via Caddy | `docker compose -f deploy/demo-compose.yml --env-file deploy/.env.demo up -d --build --wait` | Compose status and curl output | interview |
| Load-test harness supports a CI-safe synthetic smoke profile | Locust profile dry-run plus schema/assertion unit tests | synthetic benchmark questions | local development | 2026-08-23 | Smoke profile defines one user and five fake-provider requests; dry-run writes timestamped manifest without traffic | `make benchmark-smoke` | `load/reports/<timestamp>/manifest.json` generated locally; tests under `tests/load` | README/interview |
| GroundStack distinguishes simulated load from production usage claims | Claims registry and benchmark docs review | docs/benchmarks | repository documentation | 2026-08-23 | Reports require provider mode, environment, workload, limitations, and evidence paths | `make capacity-report` | `docs/benchmarks/CAPACITY_REPORT.md` | README/interview |
| Hosted-provider load testing is opt-in and capped | Runner confirmation gates and real-provider ceiling | load profiles | local development | 2026-08-23 | Requires `--confirm-real-provider` plus `GROUNDSTACK_REAL_LOAD_ALLOWED=true`; default ceiling is 10 requests | `PYTHONPATH=. python -m load.run_locust_profile --profile real-provider --confirm --confirm-real-provider` | `load/profiles.py` and runner tests | internal only |

Do not promote unmeasured claims such as public usage, production adoption, accuracy improvements,
latency reductions, 99.9% uptime, 300 real users per day, or use by a 50,000-member community.
