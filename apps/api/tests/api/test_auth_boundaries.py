import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import optional_principal
from app.main import app


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _set_unauthenticated_principal() -> None:
    async def principal():
        return None

    app.dependency_overrides[optional_principal] = principal


async def test_admin_route_rejects_unauthenticated_request() -> None:
    _set_unauthenticated_principal()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/documents")

    assert response.status_code == 401


async def test_security_headers_and_request_id_are_present() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health", headers={"x-groundstack-request-id": "rid-1"})

    assert response.status_code == 200
    assert response.headers["x-groundstack-request-id"] == "rid-1"
    assert response.headers["x-content-type-options"] == "nosniff"
