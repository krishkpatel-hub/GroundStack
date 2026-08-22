# Evaluation And Claims

GroundStack evaluation is split into deterministic suites and optional real-provider runs.

Use:

```bash
make eval
make eval-generation
make eval-security
make compare-prompts
```

The deterministic runner writes JSON reports to `evaluation/reports/` and records dataset
checksum, prompt version, retrieval configuration, model metadata, adapter metadata, git commit,
aggregate metrics, and per-case results.

Judge-based scores are not a substitute for deterministic citation, grounding, abstention, and
security checks. Do not publish an improvement claim unless the base and adapter reports were
produced from the same dataset checksum and the same evaluation runner version.

The API also has database tables for `evaluation_runs` and `evaluation_results`, exposed read-only
through `/api/v1/evaluation/runs`.
