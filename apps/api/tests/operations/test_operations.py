import pytest

from app.services.operations.metrics import MetricsRegistry
from app.services.operations.rate_limit import TokenBucketLimiter


async def test_token_bucket_returns_retry_after() -> None:
    limiter = TokenBucketLimiter(limit=1, window_seconds=60)

    assert (await limiter.check("client")).allowed is True
    second = await limiter.check("client")

    assert second.allowed is False
    assert second.retry_after_seconds > 0


def test_metrics_rejects_high_cardinality_labels() -> None:
    registry = MetricsRegistry()

    with pytest.raises(ValueError):
        registry.increment("groundstack_bad_total", user_id="abc")
