# Contributing

Use small pull requests with clear verification notes. Do not commit `.env` files, credentials,
model weights, private datasets, generated caches, or production logs.

Before opening a PR:

```bash
make lint
make typecheck
make test
npm run build --workspace apps/web
cd training && PYTHONPATH=. ../apps/api/.venv/bin/python -m pytest
```

Run migrations as a separate release task. Do not start fine-tuning or load tests against paid
providers from CI unless the owner has explicitly approved the workflow and budget.
