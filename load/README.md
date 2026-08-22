# GroundStack Load Validation

This directory contains Locust-oriented profiles for retrieval and chat capacity
testing. Synthetic/fake-provider smoke tests can be used during development.
The `real-300` profile requires explicit opt-in because it may call a real model
provider and should be archived with raw output before making any capacity claim.

Profiles:

- `fake-smoke`: short local API smoke run.
- `fake-sustained`: longer fake-provider run for backpressure behavior.
- `real-300`: 300-question policy validation. Requires `--require-real` and
  `GROUNDSTACK_REAL_LOAD_ALLOWED=true`.

The 300-questions-per-day target is validated only when 300 successful
end-to-end questions complete within 24 hours without unhandled 5xx errors,
with p95 latency, throttling counts, and provider configuration included in the
report.
