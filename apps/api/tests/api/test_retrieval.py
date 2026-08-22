from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.ai.types import Citation, RetrievalResult, RetrievalTrace


async def test_retrieval_search_response(monkeypatch) -> None:
    async def fake_retrieve(_self, query):
        return RetrievalResult(
            retrieval_run_id=uuid4(),
            normalized_query=query.text.strip(),
            result_count=1,
            evidence_found=True,
            reranking_applied=False,
            degraded_mode=None,
            applied_filters=query.filters,
            citations=[
                Citation(
                    citation_id="S1",
                    source_id=uuid4(),
                    document_id=uuid4(),
                    document_version=1,
                    chunk_id=uuid4(),
                    title="GroundStack Local Setup",
                    source_display_name="setup.md",
                    source_type="file",
                    source_uri=None,
                    section_path="Database",
                    page_number=None,
                    excerpt="Run docker compose ps.",
                    final_rank=1,
                )
            ],
            trace=RetrievalTrace(
                query_hash="a" * 64,
                query_length=16,
                final_result_count=1,
                latency_ms={"total": 1.0},
            ),
        )

    monkeypatch.setattr("app.services.retrieval.service.HybridRetriever.retrieve", fake_retrieve)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/retrieval/search",
            json={"query": " database failing ", "top_k": 3, "filters": {}},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["evidence_found"] is True
    assert body["citations"][0]["citation_id"] == "S1"


async def test_retrieval_search_rejects_empty_query(monkeypatch) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/retrieval/search", json={"query": "   "})

    assert response.status_code in {422, 500}
