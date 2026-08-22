# GroundStack Evaluation

This package records reproducible, deterministic evaluation runs for retrieval,
generation, grounding, citations, abstention, prompt-injection, security,
performance, and regression suites.

It intentionally does not claim model-quality improvements or production
capacity from synthetic runs. Real-provider validation must be run separately
and archived with the generated manifest.

Run:

```bash
make eval
make eval-generation
make eval-security
make compare-prompts
```

Reports are written to `evaluation/reports/`.
