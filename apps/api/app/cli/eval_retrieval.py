import asyncio
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from app.core.settings import Settings
from app.services.ai.types import RetrievalFilters, RetrievalQuery
from app.services.retrieval.service import HybridRetriever

DATASET_PATH = Path("dev-data/retrieval-eval.json")
RESULTS_DIR = Path("dev-data/retrieval-results")


def _dataset_checksum(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _score(
    result, expected_source: str | None, expected_section: str | None, k: int
) -> dict[str, float]:
    citations = result.citations[:k]
    if expected_source is None:
        return {"hit": 0.0, "rr": 0.0, "dcg": 0.0}
    for index, citation in enumerate(citations, start=1):
        source_match = citation.source_display_name == expected_source
        section_match = not expected_section or (
            citation.section_path is not None and citation.section_path.endswith(expected_section)
        )
        if source_match and section_match:
            return {
                "hit": 1.0,
                "rr": 1.0 / index,
                "dcg": 1.0 / math.log2(index + 1),
            }
    return {"hit": 0.0, "rr": 0.0, "dcg": 0.0}


async def _run_mode(mode: str, queries: list[dict[str, object]]) -> dict[str, object]:
    settings = Settings()
    if mode == "vector_only":
        settings.lexical_candidate_limit = 0
        settings.reranking_enabled = False
    elif mode == "lexical_only":
        settings.vector_candidate_limit = 0
        settings.reranking_enabled = False
    elif mode == "hybrid_rrf":
        settings.reranking_enabled = False
    retriever = HybridRetriever(settings=settings)
    rows = []
    for item in queries:
        result = await retriever.retrieve(
            RetrievalQuery(
                text=str(item["query"]),
                limit=10,
                filters=RetrievalFilters(),
                include_debug=False,
            )
        )
        expected_source = item.get("expected_source") if item.get("answerable") else None
        expected_section = item.get("expected_section") if item.get("answerable") else None
        rows.append(
            {
                "id": item["id"],
                "answerable": item["answerable"],
                "recall_5": _score(result, expected_source, expected_section, 5)["hit"],
                "recall_10": _score(result, expected_source, expected_section, 10)["hit"],
                "mrr_10": _score(result, expected_source, expected_section, 10)["rr"],
                "ndcg_10": _score(result, expected_source, expected_section, 10)["dcg"],
                "result_count": result.result_count,
                "degraded_mode": result.degraded_mode,
            }
        )
    answerable = [row for row in rows if row["answerable"]]
    unsupported = [row for row in rows if not row["answerable"]]
    return {
        "mode": mode,
        "metrics": {
            "answerable_count": len(answerable),
            "unsupported_count": len(unsupported),
            "recall_at_5": mean(row["recall_5"] for row in answerable) if answerable else 0.0,
            "recall_at_10": mean(row["recall_10"] for row in answerable) if answerable else 0.0,
            "mrr_at_10": mean(row["mrr_10"] for row in answerable) if answerable else 0.0,
            "ndcg_at_10": mean(row["ndcg_10"] for row in answerable) if answerable else 0.0,
            "unsupported_with_results": sum(1 for row in unsupported if row["result_count"] > 0),
        },
        "rows": rows,
    }


async def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    queries = list(dataset["queries"])
    modes = ["vector_only", "lexical_only", "hybrid_rrf", "hybrid_rerank"]
    results = [await _run_mode(mode, queries) for mode in modes]
    settings = Settings()
    payload = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": dataset["name"],
        "dataset_checksum": _dataset_checksum(dataset),
        "algorithm_version": settings.retrieval_algorithm_version,
        "embedding_model": settings.embedding_model_name,
        "reranker_model": settings.reranker_model_name,
        "results": results,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / f"retrieval-eval-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"output": str(output), "results": [item["metrics"] for item in results]},
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
