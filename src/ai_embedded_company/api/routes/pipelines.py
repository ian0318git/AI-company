"""Pipeline API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import PipelineModel
from ai_embedded_company.types import Pipeline, PipelineCreate, PipelinePhase, PipelineStep, TaskStatus

router = APIRouter()


@router.post("/", status_code=201)
async def create_pipeline(
    payload: PipelineCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create a new pipeline."""
    pipeline = PipelineModel(
        project_id=payload.project_id,
        pipeline_type=payload.pipeline_type.value if hasattr(payload.pipeline_type, 'value') else payload.pipeline_type,
        idea_id=payload.idea_id,
        steps="[]",
        current_phase="idea",
    )
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)

    return {
        "id": pipeline.id,
        "project_id": pipeline.project_id,
        "pipeline_type": pipeline.pipeline_type,
        "current_phase": pipeline.current_phase,
        "created_at": pipeline.created_at.isoformat() if pipeline.created_at else None,
    }


@router.get("/")
async def list_pipelines(
    project_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List pipelines, optionally filtered by project."""
    stmt = select(PipelineModel)
    if project_id:
        stmt = stmt.where(PipelineModel.project_id == project_id)
    result = await session.execute(stmt)
    pipelines = result.scalars().all()
    return [
        {
            "id": p.id,
            "project_id": p.project_id,
            "pipeline_type": p.pipeline_type,
            "current_phase": p.current_phase,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in pipelines
    ]


@router.get("/{pipeline_id}")
async def get_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get pipeline details."""
    result = await session.execute(
        select(PipelineModel).where(PipelineModel.id == pipeline_id)
    )
    p = result.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    try:
        steps = json.loads(p.steps) if p.steps else []
    except json.JSONDecodeError:
        steps = []

    return {
        "id": p.id,
        "project_id": p.project_id,
        "pipeline_type": p.pipeline_type,
        "current_phase": p.current_phase,
        "steps": steps,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.post("/{pipeline_id}/advance")
async def advance_pipeline(
    pipeline_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Advance the pipeline to the next phase. Auto-completes linked idea when done."""
    from ai_embedded_company.storage.models import IdeaModel

    result = await session.execute(
        select(PipelineModel).where(PipelineModel.id == pipeline_id)
    )
    p = result.scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Phase progression order
    phase_order = [ph.value for ph in PipelinePhase]
    current_idx = phase_order.index(p.current_phase) if p.current_phase in phase_order else 0
    next_idx = min(current_idx + 1, len(phase_order) - 1)
    new_phase = phase_order[next_idx]

    p.current_phase = new_phase

    # Auto-complete linked idea when pipeline reaches "done"
    if new_phase == "done" and p.idea_id:
        idea_result = await session.execute(
            select(IdeaModel).where(IdeaModel.id == p.idea_id)
        )
        idea = idea_result.scalar_one_or_none()
        if idea and idea.status != "done":
            idea.status = "done"

    await session.commit()
    await session.refresh(p)

    return {
        "id": p.id,
        "previous_phase": phase_order[current_idx],
        "current_phase": new_phase,
        "is_complete": new_phase == "done",
        "message": f"Pipeline advanced to phase: {new_phase}",
    }
