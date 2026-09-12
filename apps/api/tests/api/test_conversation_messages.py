from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.conversations import _message_response
from app.schemas.retrieval import CitationResponse


def test_message_response_includes_persisted_feedback() -> None:
    message_id = uuid4()
    conversation_id = uuid4()
    message = SimpleNamespace(
        id=message_id,
        conversation_id=conversation_id,
        role="assistant",
        status="completed",
        content="Grounded answer. [S1]",
        grounding_status="grounded",
        retrieval_run_id=None,
        generation_run_id=None,
        provider="fake",
        model="deterministic",
        prompt_version="test",
        token_usage=None,
        failure=None,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    feedback = SimpleNamespace(
        rating="positive",
        categories=[],
        comment=None,
        suggested_correction=None,
        citations_incorrect=False,
        reported_citation_ids=[],
        client_request_id="feedback-stable",
    )

    citation = CitationResponse(
        citation_id="S1",
        source_id=uuid4(),
        document_id=uuid4(),
        document_version=1,
        chunk_id=uuid4(),
        title="Configuration procedure",
        source_display_name="validation.md",
        source_type="file",
        source_uri="file://validation.md",
        section_path="Resolution",
        page_number=None,
        excerpt="Restart the worker and confirm validation_status=ready.",
        final_rank=1,
    )
    response = _message_response(message, citations=[citation], feedback=feedback)

    assert response.citations == [citation]
    assert response.citations[0].excerpt.startswith("Restart the worker")
    assert response.feedback is not None
    assert response.feedback.rating == "positive"
    assert response.feedback.client_request_id == "feedback-stable"
