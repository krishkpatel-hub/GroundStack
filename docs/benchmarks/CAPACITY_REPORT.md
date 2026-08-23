# GroundStack Capacity Report

Date: 2026-08-23  
Branch: `benchmark/reliability-evidence`  
Scope: local tooling, deterministic profiles, and safe dry-run evidence unless a live target is
explicitly supplied.

## What Was Verified

- Milestone 11 was merged into `main` before this branch was created.
- Deterministic load profiles were added for smoke, 300-request volume, burst, sustained, spike
  recovery, mixed web/Discord, Ollama, and hosted-provider modes.
- Response assertions now require valid SSE terminal events, request IDs, grounding states, and
  citation schema checks.
- Hosted-provider benchmarks require explicit confirmation and `GROUNDSTACK_REAL_LOAD_ALLOWED=true`.
- Smoke dry-runs produce timestamped manifests without sending traffic.
- Sanitized machine-readable evidence is stored in
  `docs/benchmarks/evidence/2026-08-23-smoke-dry-run.json`.

## Machine Safety Snapshot

Local probes were partially sandbox-limited. `vm_stat` showed substantial historical compression and
swap activity, Docker daemon access required approval, `ollama` was not available on PATH, and no
common GroundStack development ports were listening during the initial check. Based on the previous
out-of-application-memory warning, the safe local recommendation is:

- Docker Desktop: 4-6 GB memory, 2-4 CPUs for the normal dev stack.
- Ollama: run one small model at a time; avoid loading multiple large quantizations.
- Benchmarks: start with `make benchmark-smoke`; run burst/soak only after memory pressure is stable.
- Browsers, Docker, Ollama, and high-concurrency Locust should not run together on a constrained
  machine.

## Profiles

| Profile | Provider | Requests | Concurrency | Purpose | Safety |
| --- | --- | ---: | ---: | --- | --- |
| `smoke` | fake | 5 | 1 | CI-safe infrastructure validation | safe by default |
| `volume-300` | fake | 300 | 3 | 300-request load test, not a user claim | confirmation required |
| `burst` | fake | 80 | 8 | conservative community burst | confirmation required |
| `soak-short` | fake | 120 | 4 | short sustained leak/pool check | confirmation required |
| `soak-long` | fake | 1000 | 6 | optional extended soak | manual only |
| `spike-recovery` | fake | 150 | 12 | admission control and recovery | manual only |
| `mixed-discord` | fake | 100 | 4 | web, Discord, feedback/status mix | confirmation required |
| `ollama` | ollama | 20 | 1 | local generation sample | manual, one model |
| `real-provider` | hosted | 10 | 1 | opt-in hosted sample | explicit real-provider flag |

## Current Baselines

No live traffic baseline is claimed in this document. The generated evidence currently supports only
that the harness, profile definitions, dry-run reporting, and validation code execute locally. Any
future latency, throughput, or capacity claim must reference a timestamped `load/reports/...`
artifact and list provider mode separately.

## Backpressure And Admission Control

GroundStack currently exposes bounded generation concurrency through the existing generation gate,
demo request limits, Discord user/channel/guild limits, queue expiration, and provider timeouts. The
load profiles are designed to verify early rejection, visible failures, and recovery after queue drain
without silently accepting unbounded in-memory work.

## Resource-Leak Testing

The sustained profiles capture start/end environment snapshots. A short sustained run can flag
process memory growth, open-file growth, database/Redis connection growth, queue growth, and SSE
connection leaks, but no report should claim "no memory leaks" from one short run. Long soak evidence
must include start/end resource state and known machine constraints.

## Not Tested Yet

- Real production usage.
- Public Discord delivery reliability.
- Ollama tokens per second and stable concurrency.
- Hosted-provider latency or cost.
- Cloud database and Redis capacity.
- Long sustained soak behavior.

## Required Evidence For Future Claims

Each committed summary must include git commit, date, duration, workload profile, hardware/OS,
container limits, app configuration, DB/Redis configuration, embedding model, generation model,
provider type, prompt version, corpus version, corpus size, chunk count, concurrency, spawn rate,
warmup, total requests, success criteria, results, errors, and limitations.
