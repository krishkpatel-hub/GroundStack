from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import Principal, optional_principal
from app.main import app
from app.services.operations.feedback import FeedbackError


class FakeFeedback:
    def __init__(self, message_id):
        self.id = uuid4()
        self.message_id = message_id
        self.conversation_id = uuid4()
        self.rating = "negative"
        self.categories = ["incorrect_answer"]
        self.comment = "wrong"
        self.suggested_correction = None
        self.citations_incorrect = False
        self.reported_citation_ids = []
        self.client_request_id = "test-client"
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False

    async def commit(self):
        return None

    async def refresh(self, _row):
        return None


class FakeRepository:
    def __init__(self, _session):
        pass

    async def upsert_feedback(self, *, message_id, request, owner_subject=None):
        if str(message_id).endswith("0"):
            raise FeedbackError("Feedback can only be saved for an existing assistant message.")
        return FakeFeedback(message_id)

    async def get_feedback(self, *, message_id, client_request_id):
        return FakeFeedback(message_id)

    async def delete_feedback(self, *, message_id, client_request_id):
        return True


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _set_chat_principal() -> None:
    async def principal():
        return Principal(
            subject="test:chat-user",
            roles=frozenset(["user"]),
            authenticated=True,
        )

    app.dependency_overrides[optional_principal] = principal


async def test_feedback_put_is_idempotent_shape(monkeypatch) -> None:
    async def no_limit(_request):
        return None

    _set_chat_principal()
    monkeypatch.setattr("app.api.v1.feedback.async_session_factory", lambda: FakeSession())
    monkeypatch.setattr("app.api.v1.feedback.FeedbackRepository", FakeRepository)
    monkeypatch.setattr("app.api.v1.feedback._enforce_feedback_limit", no_limit)
    message_id = "11111111-1111-1111-1111-111111111111"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/messages/{message_id}/feedback",
            json={
                "rating": "negative",
                "categories": ["incorrect_answer"],
                "comment": "wrong",
                "citations_incorrect": False,
                "reported_citation_ids": [],
                "client_request_id": "test-client",
            },
        )

    assert response.status_code == 200
    assert response.json()["message_id"] == str(message_id)


async def test_feedback_put_rejects_invalid_message(monkeypatch) -> None:
    async def no_limit(_request):
        return None

    _set_chat_principal()
    monkeypatch.setattr("app.api.v1.feedback.async_session_factory", lambda: FakeSession())
    monkeypatch.setattr("app.api.v1.feedback.FeedbackRepository", FakeRepository)
    monkeypatch.setattr("app.api.v1.feedback._enforce_feedback_limit", no_limit)
    bad_id = "00000000-0000-0000-0000-000000000000"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/messages/{bad_id}/feedback",
            json={"rating": "positive", "client_request_id": "test-client"},
        )

    assert response.status_code == 404


async def test_feedback_put_rejects_unauthenticated_request(monkeypatch) -> None:
    async def no_limit(_request):
        return None

    monkeypatch.setattr("app.api.v1.feedback._enforce_feedback_limit", no_limit)
    message_id = "11111111-1111-1111-1111-111111111111"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/messages/{message_id}/feedback",
            json={"rating": "positive", "client_request_id": "test-client"},
        )

    assert response.status_code == 401
