from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

FeedbackRating = Literal["positive", "negative"]
FeedbackCategory = Literal[
    "incorrect_answer",
    "incomplete_answer",
    "irrelevant_sources",
    "missing_citation",
    "incorrect_citation",
    "unsupported_claim",
    "unsafe_response",
    "too_verbose",
    "too_vague",
    "slow_response",
    "other",
]


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.replace("\x00", "").split())


class FeedbackRequest(BaseModel):
    rating: FeedbackRating
    categories: list[FeedbackCategory] = Field(default_factory=list, max_length=10)
    comment: str | None = Field(default=None, max_length=1000)
    suggested_correction: str | None = Field(default=None, max_length=3000)
    citations_incorrect: bool = False
    reported_citation_ids: list[str] = Field(default_factory=list, max_length=20)
    client_request_id: str = Field(..., min_length=1, max_length=120)

    @field_validator("comment", "suggested_correction")
    @classmethod
    def sanitize_text(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("reported_citation_ids")
    @classmethod
    def bounded_citations(cls, value: list[str]) -> list[str]:
        return sorted({item.strip().upper() for item in value if item.strip()})[:20]


class FeedbackResponse(BaseModel):
    id: UUID
    message_id: UUID
    conversation_id: UUID
    rating: str
    categories: list[str]
    comment: str | None
    suggested_correction: str | None
    citations_incorrect: bool
    reported_citation_ids: list[str]
    client_request_id: str
    created_at: datetime
    updated_at: datetime
