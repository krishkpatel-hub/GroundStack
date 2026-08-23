# GroundStack SLO Proposal

This is a proposal template, not an uptime claim. Targets remain provisional until a baseline load
test has produced timestamped evidence in `load/reports/`.

| Indicator | User impact | Query sketch | Window | Exclusions | Baseline | Proposed target |
| --- | --- | --- | --- | --- | --- | --- |
| API availability | Users can reach health and chat routes | `sum(rate(http_requests_total{status!~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | 7d | planned maintenance | not measured | unset |
| Successful request processing | Answers complete or fail visibly | `successful_answers / accepted_questions` | 24h | user cancellations | not measured | unset |
| Retrieval latency | Citations appear quickly | histogram p95 for retrieval operation | 24h | empty corpus setup | not measured | unset |
| Time to first token | Streaming feels responsive | p95 first-token latency | 24h | provider outage | not measured | unset |
| Complete-answer latency | Full answer arrives in tolerable time | p95 completed chat latency | 24h | cancellations | not measured | unset |
| Citation validation success | Grounded answers are supported | validation failures / generations | 24h | insufficient evidence | not measured | unset |
| Discord acknowledgment | Discord does not time out commands | p99 interaction ack latency | 24h | invalid signatures | not measured | unset |
| Queue wait | Backlog remains bounded | p95 queue wait | 1h | disabled integration | not measured | unset |
| Recovery after dependency failure | Service recovers after local fault | failure-test recovery time | scenario | injected fault period | not measured | unset |

## Dashboard Panels

- Request throughput by route and status.
- p50/p95/p99 latency by operation.
- Active generations and generation backpressure rejections.
- Queue depth and queue wait.
- Provider failures by low-cardinality category.
- Citation-validation failures.
- Redis and database readiness.

Metric labels must not include user IDs, guild IDs, questions, answers, document content,
conversation IDs, or request IDs.
