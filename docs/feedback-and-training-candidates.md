# Feedback And Training Candidates

Feedback is stored per assistant message and client request ID. Updates are idempotent and
comments/corrections are bounded and sanitized. Because GroundStack does not yet have
authentication, feedback access is documented as local/single-user only.

Positive feedback does not make an answer trainable. Training examples require explicit human
review:

```bash
make review-training-candidates
cd apps/api && . .venv/bin/activate && python -m app.cli.review_training_candidates update <candidate-id> --redaction-status approved --provenance-status approved --status approved --reviewer <name>
make export-approved-training-data
```

Only candidates with approved status, approved redaction, and approved provenance are exported to
Prompt 6's canonical JSONL format.
