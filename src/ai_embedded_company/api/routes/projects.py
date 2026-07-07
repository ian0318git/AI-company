"""Project CRUD routes with time analytics."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import ProjectModel, TaskModel
from ai_embedded_company.types import Project, ProjectCreate, ProjectStatus

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.utcnow()


def _compute_elapsed_minutes(task: TaskModel, now: datetime) -> float | None:
    """Mirror of tasks.py helper to avoid circular imports."""
    if task.started_at is None:
        return None
    end = task.completed_at or now
    paused = task.paused_seconds or 0
    if task.last_paused_at is not None:
        paused += int((now - task.last_paused_at).total_seconds())
    total_seconds = (end - task.started_at).total_seconds() - paused
    return max(0.0, total_seconds / 60.0)


@router.post("/", response_model=Project, status_code=201)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    """Create a new project."""
    project = ProjectModel(
        name=payload.name,
        description=payload.description,
        board_family=payload.board_family.value if payload.board_family else "unknown",
        board_model=payload.board_model or "",
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return _model_to_project(project)


@router.get("/", response_model=list[Project])
async def list_projects(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Project]:
    """List all projects, optionally filtered by status."""
    stmt = select(ProjectModel)
    if status:
        stmt = stmt.where(ProjectModel.status == status)
    stmt = stmt.order_by(ProjectModel.created_at.desc())
    result = await session.execute(stmt)
    models = result.scalars().all()
    return [_model_to_project(m) for m in models]


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> Project:
    """Get a single project by ID."""
    result = await session.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _model_to_project(model)


@router.get("/{project_id}/time")
async def get_project_time(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get time analytics for a project: total time, per-agent breakdown, task stats."""
    # Verify project exists
    result = await session.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Load all tasks for this project
    task_result = await session.execute(
        select(TaskModel).where(TaskModel.project_id == project_id)
    )
    tasks = task_result.scalars().all()
    now = _utcnow()

    total_minutes = 0.0
    agent_time: dict[str, float] = {}
    agent_tokens: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    tracked_tasks = 0
    completed_tasks = 0
    total_tokens = 0

    for task in tasks:
        # Status counts
        s = task.status or "todo"
        status_counts[s] = status_counts.get(s, 0) + 1

        elapsed = _compute_elapsed_minutes(task, now)
        if elapsed is None:
            continue

        tracked_tasks += 1
        total_minutes += elapsed

        if task.status == "done" and task.completed_at:
            completed_tasks += 1

        # Per-agent aggregation
        agent = task.assigned_agent or "unassigned"
        agent_time[agent] = agent_time.get(agent, 0.0) + elapsed
        tokens = task.tokens_used or 0
        agent_tokens[agent] = agent_tokens.get(agent, 0) + tokens
        total_tokens += tokens

    # Format agent breakdown
    agent_breakdown = [
        {"agent": agent, "minutes": round(minutes, 1)}
        for agent, minutes in sorted(agent_time.items(), key=lambda x: -x[1])
    ]

    token_breakdown = [
        {"agent": agent, "tokens": t}
        for agent, t in sorted(agent_tokens.items(), key=lambda x: -x[1])
    ]

    return {
        "project_id": project_id,
        "project_name": project.name,
        "project_status": project.status,
        "total_tasks": len(tasks),
        "tracked_tasks": tracked_tasks,
        "completed_tasks": completed_tasks,
        "total_minutes": round(total_minutes, 1),
        "total_minutes_formatted": _format_minutes(total_minutes),
        "agent_breakdown": agent_breakdown,
        "token_breakdown": token_breakdown,
        "total_tokens": total_tokens,
        "status_counts": status_counts,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "completed_at": project.updated_at.isoformat() if project.status == "completed" else None,
    }


@router.patch("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    """Update a project."""
    result = await session.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Project not found")

    model.name = payload.name
    model.description = payload.description
    if payload.board_family:
        model.board_family = payload.board_family.value
    model.board_model = payload.board_model or ""

    await session.commit()
    await session.refresh(model)
    return _model_to_project(model)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a project and all associated data."""
    result = await session.execute(
        select(ProjectModel).where(ProjectModel.id == project_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(model)
    await session.commit()


def _model_to_project(m: ProjectModel) -> Project:
    """Convert ORM model to Pydantic schema."""
    return Project(
        id=m.id,
        name=m.name,
        description=m.description,
        status=ProjectStatus(m.status),
        board_family=m.board_family,
        board_model=m.board_model,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _format_minutes(minutes: float) -> str:
    """Format minutes into human-readable string."""
    if minutes < 1:
        return "<1m"
    if minutes < 60:
        return f"{round(minutes)}m"
    h = int(minutes // 60)
    m = round(minutes % 60)
    return f"{h}h {m}m" if m > 0 else f"{h}h"
