"""Task CRUD routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import TaskModel
from ai_embedded_company.types import Task, TaskCreate, TaskPriority, TaskStatus

router = APIRouter()


@router.post("/", response_model=Task, status_code=201)
async def create_task(
    payload: TaskCreate,
    session: AsyncSession = Depends(get_session),
) -> Task:
    """Create a new task."""
    task = TaskModel(
        project_id=payload.project_id,
        parent_task_id=payload.parent_task_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        assigned_agent=payload.assigned_agent.value if payload.assigned_agent else None,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return _model_to_task(task)


@router.get("/", response_model=list[Task])
async def list_tasks(
    project_id: str | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Task]:
    """List tasks, optionally filtered by project and/or status."""
    stmt = select(TaskModel)
    if project_id:
        stmt = stmt.where(TaskModel.project_id == project_id)
    if status:
        stmt = stmt.where(TaskModel.status == status)
    stmt = stmt.order_by(TaskModel.priority.desc(), TaskModel.created_at.asc())
    result = await session.execute(stmt)
    models = result.scalars().all()
    return [_model_to_task(m) for m in models]


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> Task:
    """Get a single task by ID."""
    result = await session.execute(
        select(TaskModel).where(TaskModel.id == task_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _model_to_task(model)


@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: str,
    status: str,
    session: AsyncSession = Depends(get_session),
) -> Task:
    """Update a task's status. Auto-advances pipeline when all tasks are done."""
    valid = {s.value for s in TaskStatus}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    result = await session.execute(
        select(TaskModel).where(TaskModel.id == task_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Task not found")

    model.status = status
    await session.flush()

    # Auto-advance pipeline when all tasks in the project are done
    if status == "done":
        await _auto_advance_if_all_done(session, model.project_id)

    await session.commit()
    await session.refresh(model)
    return _model_to_task(model)


async def _auto_advance_if_all_done(session, project_id: str):
    """If every task in this project is done, advance the pipeline one phase."""
    from ai_embedded_company.storage.models import PipelineModel

    # Check if any non-done tasks remain
    remaining = await session.execute(
        select(TaskModel).where(
            TaskModel.project_id == project_id,
            TaskModel.status != "done",
        )
    )
    if remaining.scalars().first() is not None:
        return  # Not all done yet

    # Find the active (non-done) pipeline for this project.
    # A project may have multiple pipelines (e.g. re-runs); pick the one that
    # is not yet at "done", or fall back to the most recently created one.
    pipe_result = await session.execute(
        select(PipelineModel)
        .where(PipelineModel.project_id == project_id)
        .order_by(PipelineModel.created_at.desc())
    )
    pipelines = pipe_result.scalars().all()
    # Prefer the active pipeline; if all are done there is nothing to advance
    pipeline = next((p for p in pipelines if p.current_phase != "done"), None)
    if pipeline is None:
        return  # No active pipeline to advance

    # Advance to next phase
    phase_order = ["idea", "requirements", "design", "implementation", "testing", "deploy", "done"]
    current_idx = phase_order.index(pipeline.current_phase) if pipeline.current_phase in phase_order else 0
    next_idx = min(current_idx + 1, len(phase_order) - 1)
    pipeline.current_phase = phase_order[next_idx]

    # If advancing to "done", also mark the linked idea as done
    if phase_order[next_idx] == "done" and pipeline.idea_id:
        from ai_embedded_company.storage.models import IdeaModel
        idea_result = await session.execute(
            select(IdeaModel).where(IdeaModel.id == pipeline.idea_id)
        )
        idea = idea_result.scalar_one_or_none()
        if idea and idea.status != "done":
            idea.status = "done"


def _model_to_task(m: TaskModel) -> Task:
    """Convert ORM model to Pydantic schema."""
    return Task(
        id=m.id,
        project_id=m.project_id,
        parent_task_id=m.parent_task_id,
        title=m.title,
        description=m.description,
        status=TaskStatus(m.status),
        priority=TaskPriority(m.priority),
        assigned_agent=m.assigned_agent,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )
