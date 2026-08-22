from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvaluationRunResponse(BaseModel):
    id: UUID
    name: str
    status: str
    suite_names: list[str]
    dataset_version: str
    dataset_checksum: str
    model_metadata: dict[str, object]
    prompt_version: str
    retrieval_configuration: dict[str, object]
    environment_metadata: dict[str, object]
    aggregate_metrics: dict[str, object] | None
    failure: dict[str, object] | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class EvaluationResultResponse(BaseModel):
    id: UUID
    evaluation_run_id: UUID
    test_case_id: str
    question_category: str | None
    expected_answerability: str | None
    deterministic_metrics: dict[str, object]
    judge_metrics: dict[str, object] | None
    passed: bool
    failure_reasons: list[str]
    latency_ms: float | None
    created_at: datetime
