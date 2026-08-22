# Observability

GroundStack exposes Prometheus-compatible metrics at `/api/v1/metrics`.

Defaults:

- Metrics are enabled for local development.
- Without `METRICS_INTERNAL_TOKEN`, metrics are local-only.
- Set `METRICS_INTERNAL_TOKEN` before exposing the API outside localhost.
- Metric labels are allowlisted to avoid user IDs, prompts, messages, or other high-cardinality or
  private values.

The tracing shim keeps a safe attribute allowlist and can be replaced by a full OpenTelemetry
exporter when `OTEL_TRACING_ENABLED=true` and an `OTLP_ENDPOINT` are configured.

Optional local observability services can be started with Docker Compose's `observability` profile:

```bash
docker compose --profile observability up -d prometheus grafana
```
