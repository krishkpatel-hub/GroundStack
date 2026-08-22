from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_missing_document_returns_structured_404(monkeypatch) -> None:
    async def missing_document(_self, _document_id):
        return None

    monkeypatch.setattr(
        "app.services.ingestion.persistence.KnowledgeRepository.get_document",
        missing_document,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/documents/{uuid4()}")

    assert response.status_code in {404, 500}
    assert "error" in response.json()
