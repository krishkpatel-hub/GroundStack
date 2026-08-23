# GroundStack Load Validation

This directory contains deterministic Locust profiles and report helpers for reliability,
capacity, and evidence-backed claims. Synthetic traffic is not production usage and must not be
described as real adoption.

## Safe Defaults

```bash
make benchmark-smoke
```

`benchmark-smoke` runs a dry-run by default and writes a timestamped manifest under
`load/reports/`. To send traffic, provide a live local target:

```bash
PYTHONPATH=. python -m load.run_locust_profile --profile smoke --host http://localhost:8000
```

## Profiles

- `smoke`: one user, five questions, fake provider, CI-safe.
- `volume-300`: exactly 300 synthetic requests. This is a 300-request load test, not 300 users or
  300 real daily questions.
- `burst`: sudden small group of users for backpressure and rate-limit behavior.
- `soak-short`: short sustained developer preset.
- `soak-long`: optional longer sustained run.
- `spike-recovery`: rapid increase followed by recovery observation.
- `mixed-discord`: web chat, retrieval, status, and invalid-signature Discord interaction checks.
- `ollama`: local generation run with one Ollama model at a time.
- `real-provider`: hosted-provider sample, opt-in only.

Moderate and aggressive profiles require `--confirm`. Hosted-provider runs also require
`--confirm-real-provider` and `GROUNDSTACK_REAL_LOAD_ALLOWED=true`.

## Evidence

Every run writes:

- `manifest.json`
- `summary.json`
- Locust CSV output for real traffic runs

Reports must record environment, profile, provider mode, corpus version, concurrency, spawn rate,
request ceiling, success criteria, results, errors, and limitations.

Raw `load/reports/` artifacts may contain operational details and remain ignored. Commit only
sanitized summaries under `docs/benchmarks/` when they are reviewed.
