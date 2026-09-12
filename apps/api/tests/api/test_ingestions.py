from types import SimpleNamespace

from httpx import ASGITransport, AsyncClient

from app.core.auth import Principal, optional_principal
from app.main import app


def _set_admin_principal() -> None:
    async def principal() -> Principal:
        return Principal(
            subject="test:admin",
            roles=frozenset(["admin"]),
            authenticated=True,
        )

    app.dependency_overrides[optional_principal] = principal


async def test_file_ingestion_rejects_unsupported_type() -> None:
    _set_admin_principal()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ingestions/files",
                files={"file": ("payload.exe", b"not a document", "application/octet-stream")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Unsupported file type."


async def test_file_ingestion_rejects_oversized_payload(monkeypatch) -> None:
    _set_admin_principal()
    monkeypatch.setattr(
        "app.api.v1.ingestions.get_settings",
        lambda: SimpleNamespace(max_ingestion_file_size_bytes=4),
    )
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/ingestions/files",
                files={"file": ("too-large.txt", b"12345", "text/plain")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 413
    assert response.json()["error"]["message"] == "File exceeds maximum ingestion size."
