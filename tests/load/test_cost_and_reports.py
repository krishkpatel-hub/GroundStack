from scripts.capacity_report import baseline_payload, validate_payload
from scripts.cost_model import Pricing, Usage, estimate


def test_capacity_report_baseline_matches_schema() -> None:
    assert validate_payload(baseline_payload()) == []


def test_cost_estimate_separates_model_and_infra() -> None:
    result = estimate(
        Pricing(
            provider="test",
            model="test-model",
            effective_date="2026-08-23",
            source_url="https://example.com",
            currency="USD",
            input_per_million_tokens=1.0,
            output_per_million_tokens=2.0,
            embedding_per_million_tokens=0.1,
        ),
        Usage(
            questions_per_day=100,
            average_prompt_tokens=1000,
            average_completion_tokens=500,
            embedding_tokens_per_day=10000,
            cache_hit_rate=0.0,
            database_monthly=30,
            redis_monthly=10,
            backend_monthly=20,
            worker_monthly=5,
            storage_monthly=1,
            transfer_monthly=1,
        ),
    )

    assert result["currency"] == "USD"
    assert result["estimated_monthly_cost"] > result["infrastructure_monthly"]
