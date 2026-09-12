from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.core.auth import Principal, optional_principal
from app.main import app


async def test_missing_document_returns_structured_404(monkeypatch) -> None:
    async def missing_document(_self, _document_id):
        return None

    monkeypatch.setattr(
        "app.services.ingestion.persistence.KnowledgeRepository.get_document",
        missing_document,
    )
    transport = ASGITransport(app=app)
    _set_test_principal(role="admin")
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/documents/{uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Document not found."


def _set_test_principal(*, role: str | None) -> None:
    async def principal():
        if role is None:
            return None
        return Principal(
            subject="test:user",
            roles=frozenset([role]),
            authenticated=True,
        )

    app.dependency_overrides[optional_principal] = principal


async def test_delete_document_requires_admin() -> None:
    document_id = uuid4()
    transport = ASGITransport(app=app)
    _set_test_principal(role=None)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            unauthenticated = await client.delete(f"/api/v1/documents/{document_id}")
    finally:
        app.dependency_overrides.clear()

    assert unauthenticated.status_code == 401

    _set_test_principal(role="user")
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            forbidden = await client.delete(f"/api/v1/documents/{document_id}")
    finally:
        app.dependency_overrides.clear()

    assert forbidden.status_code == 403


async def test_delete_document_removes_document_and_chunks(monkeypatch) -> None:
    document_id = uuid4()
    calls: list[str] = []

    class FakeRepository:
        def __init__(self, _session):
            pass

        async def get_document(self, requested_document_id):
            assert requested_document_id == document_id
            return object()

        async def delete_document(self, _document):
            calls.append("deleted")

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_exc):
            return False

        async def commit(self):
            calls.append("committed")

    _set_test_principal(role="admin")
    monkeypatch.setattr("app.api.v1.documents.async_session_factory", lambda: FakeSession())
    monkeypatch.setattr("app.api.v1.documents.KnowledgeRepository", FakeRepository)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/documents/{document_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert calls == ["deleted", "committed"]
