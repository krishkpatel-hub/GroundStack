# Cost Model

GroundStack cost output is an estimate, not billing evidence.

Run:

```bash
make capacity-cost
```

The estimator reads `docs/benchmarks/cost_inputs.example.json` by default. Replace the pricing and
infrastructure inputs with user-supplied values before making any cost statement.

## Inputs

- Questions per day.
- Average prompt tokens.
- Average completion tokens.
- Embedding volume.
- Cache-hit rate.
- Model pricing entered by the user.
- Database, Redis, backend, worker, storage, and data-transfer plans.
- Provider, model, effective date, source URL, and currency.

## Outputs

- Estimated daily cost.
- Estimated monthly cost.
- Estimated cost per 100 questions.
- Model-provider share.
- Infrastructure share.
- Best-case and worst-case ranges.

Do not hard-code provider prices as permanently accurate. Do not claim actual operating cost without
real billing evidence.
