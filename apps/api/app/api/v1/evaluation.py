from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc, select

from app.core.auth import AdminPrincipal
from app.db.session import async_session_factory
from app.models.conversation import EvaluationResult, EvaluationRun
from app.schemas.evaluation import EvaluationResultResponse, EvaluationRunResponse

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/runs", response_model=list[EvaluationRunResponse])
async def list_evaluation_runs(
    _principal: AdminPrincipal,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EvaluationRunResponse]:
    async with async_session_factory() as session:
        rows = await session.execute(
            select(EvaluationRun)
            .order_by(desc(EvaluationRun.created_at))
            .limit(limit)
            .offset(offset)
        )
        return [
            EvaluationRunResponse.model_validate(row, from_attributes=True)
            for row in rows.scalars()
        ]


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run(
    run_id: UUID,
    _principal: AdminPrincipal,
) -> EvaluationRunResponse:
    async with async_session_factory() as session:
        run = await session.get(EvaluationRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Evaluation run not found.")
        return EvaluationRunResponse.model_validate(run, from_attributes=True)


@router.get("/runs/{run_id}/results", response_model=list[EvaluationResultResponse])
async def list_evaluation_results(
    run_id: UUID,
    _principal: AdminPrincipal,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EvaluationResultResponse]:
    async with async_session_factory() as session:
        if await session.get(EvaluationRun, run_id) is None:
            raise HTTPException(status_code=404, detail="Evaluation run not found.")
        rows = await session.execute(
            select(EvaluationResult)
            .where(EvaluationResult.evaluation_run_id == run_id)
            .order_by(EvaluationResult.test_case_id)
            .limit(limit)
            .offset(offset)
        )
        return [
            EvaluationResultResponse.model_validate(row, from_attributes=True)
            for row in rows.scalars()
        ]
