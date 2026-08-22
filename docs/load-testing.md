# Load Testing And Capacity Validation

Run local smoke profiles with:

```bash
make load-smoke-fake
make load-sustained-fake
```

The real 300-question validation is intentionally gated:

```bash
GROUNDSTACK_REAL_LOAD_ALLOWED=true make load-300-real
```

GroundStack may claim support for 300 questions per day only after a real provider run completes
300 end-to-end chat questions within 24 hours, with no unhandled 5xx errors, archived raw Locust CSV
output, p95 latency, throttling counts, provider/model settings, hardware/runtime metadata, and git
commit.

Synthetic fake-provider smoke tests prove route behavior and backpressure, not real model capacity.
