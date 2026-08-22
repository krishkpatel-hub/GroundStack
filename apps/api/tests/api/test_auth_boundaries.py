from httpx import ASGITransport, AsyncClient

from app.main import app


class FakeRows:
    def scalars(self):
        return []


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False

    async def execute(self, _query):
        return FakeRows()


async def test_admin_route_allows_development_admin(monkeypatch) -> None:
    monkeypatch.setattr("app.api.v1.evaluation.async_session_factory", lambda: FakeSession())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/evaluation/runs")

    assert response.status_code == 200


async def test_admin_route_rejects_non_admin_development_user() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/evaluation/runs", headers={"x-groundstack-dev-role": "user"}
        )

    assert response.status_code == 403


async def test_security_headers_and_request_id_are_present() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health", headers={"x-groundstack-request-id": "rid-1"})

    assert response.status_code == 200
    assert response.headers["x-groundstack-request-id"] == "rid-1"
    assert response.headers["x-content-type-options"] == "nosniff"
