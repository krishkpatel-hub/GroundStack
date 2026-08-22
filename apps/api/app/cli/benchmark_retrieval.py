import asyncio
from statistics import median, quantiles
from time import perf_counter

from app.core.settings import Settings
from app.services.ai.types import RetrievalFilters, RetrievalQuery
from app.services.retrieval.service import HybridRetriever

QUERIES = [
    "database connection is offline",
    "NEXT_PUBLIC_API_BASE_URL",
    "validation_error public response",
    "make ingest-sample empty knowledge base",
]


def _p95(values: list[float]) -> float:
    if len(values) < 2:
        return values[0] if values else 0.0
    return quantiles(values, n=20)[18]


async def main() -> None:
    settings = Settings()
    retriever = HybridRetriever(settings=settings)
    cold_start = perf_counter()
    await retriever.retrieve(
        RetrievalQuery(text=QUERIES[0], limit=5, filters=RetrievalFilters(), include_debug=False)
    )
    cold_ms = (perf_counter() - cold_start) * 1000

    totals: list[float] = []
    stage_values: dict[str, list[float]] = {}
    for query in QUERIES:
        result = await retriever.retrieve(
            RetrievalQuery(text=query, limit=5, filters=RetrievalFilters(), include_debug=False)
        )
        totals.append(result.trace.latency_ms["total"])
        for stage, value in result.trace.latency_ms.items():
            stage_values.setdefault(stage, []).append(value)

    print(
        {
            "cold_start_ms": round(cold_ms, 3),
            "warm_total_median_ms": round(median(totals), 3),
            "warm_total_p95_ms": round(_p95(totals), 3),
            "stages": {
                stage: {
                    "median_ms": round(median(values), 3),
                    "p95_ms": round(_p95(values), 3),
                }
                for stage, values in sorted(stage_values.items())
            },
            "query_count": len(QUERIES),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
