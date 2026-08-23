import pytest

from app.models.conversation import MessageFeedback, TrainingCandidate
from app.services.operations.feedback import FeedbackError


def test_discord_feedback_defaults_to_training_ineligible() -> None:
    feedback = MessageFeedback(
        message_id="00000000-0000-0000-0000-000000000001",
        conversation_id="00000000-0000-0000-0000-000000000002",
        rating="positive",
        client_request_id="discord-test",
        message_snapshot={},
        source_platform="discord",
        training_eligible=False,
    )

    assert feedback.source_platform == "discord"
    assert feedback.training_eligible is False


def test_discord_candidate_cannot_be_approved_by_policy() -> None:
    candidate = TrainingCandidate(
        message_id="00000000-0000-0000-0000-000000000001",
        status="pending",
        proposed_question="question",
        proposed_answer="answer",
        source_platform="discord",
        training_eligible=False,
    )

    with pytest.raises(FeedbackError):
        if candidate.source_platform == "discord" or not candidate.training_eligible:
            raise FeedbackError("Discord data cannot be approved for training.")
