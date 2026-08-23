from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pricing:
    provider: str
    model: str
    effective_date: str
    source_url: str
    currency: str
    input_per_million_tokens: float
    output_per_million_tokens: float
    embedding_per_million_tokens: float


@dataclass(frozen=True)
class Usage:
    questions_per_day: int
    average_prompt_tokens: int
    average_completion_tokens: int
    embedding_tokens_per_day: int
    cache_hit_rate: float
    database_monthly: float
    redis_monthly: float
    backend_monthly: float
    worker_monthly: float
    storage_monthly: float
    transfer_monthly: float


def estimate(pricing: Pricing, usage: Usage) -> dict[str, float | str]:
    effective_questions = usage.questions_per_day * (1 - usage.cache_hit_rate)
    input_daily = (
        effective_questions
        * usage.average_prompt_tokens
        * pricing.input_per_million_tokens
        / 1_000_000
    )
    output_daily = (
        effective_questions
        * usage.average_completion_tokens
        * pricing.output_per_million_tokens
        / 1_000_000
    )
    embedding_daily = (
        usage.embedding_tokens_per_day * pricing.embedding_per_million_tokens / 1_000_000
    )
    infra_monthly = sum(
        [
            usage.database_monthly,
            usage.redis_monthly,
            usage.backend_monthly,
            usage.worker_monthly,
            usage.storage_monthly,
            usage.transfer_monthly,
        ]
    )
    model_daily = input_daily + output_daily + embedding_daily
    daily = model_daily + infra_monthly / 30
    monthly = model_daily * 30 + infra_monthly
    return {
        "currency": pricing.currency,
        "estimated_daily_cost": round(daily, 4),
        "estimated_monthly_cost": round(monthly, 2),
        "estimated_cost_per_100_questions": round(daily / max(1, usage.questions_per_day) * 100, 4),
        "model_provider_daily": round(model_daily, 4),
        "infrastructure_monthly": round(infra_monthly, 2),
        "best_case_monthly": round(monthly * 0.75, 2),
        "worst_case_monthly": round(monthly * 1.5, 2),
    }


def _load(path: Path) -> tuple[Pricing, Usage]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return Pricing(**payload["pricing"]), Usage(**payload["usage"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate GroundStack benchmark operating cost.")
    parser.add_argument(
        "--input", type=Path, default=Path("docs/benchmarks/cost_inputs.example.json")
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    pricing, usage = _load(args.input)
    result = {
        "pricing": asdict(pricing),
        "usage": asdict(usage),
        "estimate": estimate(pricing, usage),
        "label": "estimate only; not billing evidence",
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
