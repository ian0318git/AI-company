"""Task CRUD routes with time tracking and auto-evolution."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.config import get_settings
from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import FailureRecord, TaskModel
from ai_embedded_company.types import Task, TaskCreate, TaskPriority, TaskStatus

router = APIRouter()

# ── Helpers ────────────────────────────────────────────────────────────────


def _utcnow() -> datetime:
    """Return naive UTC datetime (matching SQLite storage convention)."""
    return datetime.utcnow()


def _compute_elapsed_minutes(model: TaskModel, now: datetime | None = None) -> float | None:
    """Compute actual working minutes for a task, subtracting paused time.

    Returns None if the task was never started (started_at is None).
    All datetimes are naive UTC (SQLite convention).
    """
    if model.started_at is None:
        return None
    now = now or _utcnow()
    end = model.completed_at or now
    paused = model.paused_seconds or 0
    if model.last_paused_at is not None:
        paused += int((now - model.last_paused_at).total_seconds())
    total_seconds = (end - model.started_at).total_seconds() - paused
    return max(0.0, total_seconds / 60.0)


async def _trigger_evolution_if_slow(
    session: AsyncSession, model: TaskModel, elapsed_minutes: float
) -> None:
    """Auto-report a timeout failure if the task took too long."""
    settings = get_settings()
    threshold = float(settings.slow_task_threshold_minutes)
    if model.estimated_minutes:
        threshold = float(model.estimated_minutes) * 2.0

    if elapsed_minutes <= threshold:
        return  # Not slow enough — skip

    now = _utcnow()
    title = f"Slow task: {model.title[:60]}"
    description = (
        f"Task '{model.title}' (id={model.id}) took {elapsed_minutes:.0f} minutes "
        f"to complete, exceeding the threshold of {threshold:.0f} minutes. "
        f"Estimated: {model.estimated_minutes or 'N/A'} min."
    )
    root_cause = (
        f"Task exceeded time threshold: {elapsed_minutes:.0f} min vs {threshold:.0f} min threshold"
    )

    # Look for an existing timeout failure for the same agent + project
    existing_result = await session.execute(
        select(FailureRecord).where(
            FailureRecord.category == "timeout",
            FailureRecord.agent_role == model.assigned_agent,
            FailureRecord.project_id == model.project_id,
        ).order_by(FailureRecord.created_at.desc()).limit(1)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.frequency = (existing.frequency or 1) + 1
        existing.description = (
            f"{existing.description}\n\n--- {now.isoformat()} ---\n{description}"
        )
        if elapsed_minutes > threshold * 2 and existing.severity != "critical":
            existing.severity = "high"
        existing.updated_at = now
    else:
        severity = "high" if elapsed_minutes > threshold * 2 else "medium"
        record = FailureRecord(
            task_id=model.id,
            project_id=model.project_id,
            agent_role=model.assigned_agent,
            title=title,
            description=description,
            root_cause=root_cause,
            category="timeout",
            severity=severity,
            frequency=1,
            tags=json.dumps(["timeout", "slow-task", "auto-detected"]),
            status="reported",
        )
        session.add(record)

    await session.flush()


async def _check_slow_tasks_background(interval_seconds: int = 300) -> None:
    """Periodically check for in_progress tasks exceeding the time threshold."""
    from ai_embedded_company.storage.database import _get_sessionmaker

    while True:
        try:
            sessionmaker = _get_sessionmaker()
            async with sessionmaker() as session:
                settings = get_settings()
                threshold = float(settings.slow_task_threshold_minutes)
                now = _utcnow()

                result = await session.execute(
                    select(TaskModel).where(TaskModel.status == "in_progress")
                )
                for task in result.scalars().all():
                    elapsed = _compute_elapsed_minutes(task, now)
                    if elapsed is not None and elapsed > threshold:
                        await _trigger_evolution_if_slow(session, task, elapsed)

                await session.commit()
        except Exception:
            pass  # Non-critical — retry next interval

        import asyncio
        await asyncio.sleep(interval_seconds)


# ── CRUD Endpoints ─────────────────────────────────────────────────────────


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
        estimated_minutes=payload.estimated_minutes,
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


# ── Time Tracking Endpoints (MUST be before /{task_id} catch-all) ──────────


@router.get("/metrics")
async def task_metrics(
    project_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return aggregated time-tracking metrics for dashboard display."""
    now = _utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    stmt = select(TaskModel)
    if project_id:
        stmt = stmt.where(TaskModel.project_id == project_id)
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    today_minutes = 0.0
    total_completed = 0
    total_completed_minutes = 0.0
    slow_tasks: list[dict] = []
    active_tasks: list[dict] = []
    agent_time: dict[str, float] = {}
    status_counts: dict[str, int] = {}

    settings = get_settings()
    global_threshold = float(settings.slow_task_threshold_minutes)

    for task in tasks:
        elapsed = _compute_elapsed_minutes(task, now)
        if elapsed is None:
            # Still count status even without time
            s = task.status or "todo"
            status_counts[s] = status_counts.get(s, 0) + 1
            continue

        # Status counts
        s = task.status or "todo"
        status_counts[s] = status_counts.get(s, 0) + 1

        # Time logged today
        if task.started_at and task.started_at >= today_start:
            today_minutes += elapsed
        elif task.completed_at and task.completed_at >= today_start:
            today_minutes += elapsed

        # Completed task stats
        if task.status == "done" and task.completed_at:
            total_completed += 1
            total_completed_minutes += elapsed

        # Per-agent time
        agent = task.assigned_agent or "unassigned"
        agent_time[agent] = agent_time.get(agent, 0.0) + elapsed

        # Slow task check (only for in_progress tasks)
        if task.status == "in_progress":
            threshold = float(task.estimated_minutes) * 2.0 if task.estimated_minutes else global_threshold
            is_slow = elapsed > threshold
            active_tasks.append({
                "id": task.id,
                "title": task.title,
                "elapsed_minutes": round(elapsed, 1),
                "is_slow": is_slow,
            })
            if is_slow:
                slow_tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "elapsed_minutes": round(elapsed, 1),
                })
            if is_slow:
                slow_tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "elapsed_minutes": round(elapsed, 1),
                })

    avg_minutes = round(total_completed_minutes / total_completed, 1) if total_completed > 0 else None

    # Format agent breakdown sorted by time
    agent_breakdown = [
        {"agent": agent, "minutes": round(m, 1)}
        for agent, m in sorted(agent_time.items(), key=lambda x: -x[1])
    ]

    return {
        "total_tasks_tracked": sum(1 for t in tasks if t.started_at),
        "today_minutes": round(today_minutes, 1),
        "completed_count": total_completed,
        "average_completion_minutes": avg_minutes,
        "active_count": len(active_tasks),
        "slow_count": len(slow_tasks),
        "slow_tasks": slow_tasks,
        "active_tasks": active_tasks,
        "agent_breakdown": agent_breakdown,
        "status_counts": status_counts,
    }


@router.get("/{task_id}/time")
async def get_task_time(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return detailed time-tracking info for a single task."""
    result = await session.execute(
        select(TaskModel).where(TaskModel.id == task_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Task not found")

    now = _utcnow()
    elapsed = _compute_elapsed_minutes(model, now)

    is_slow = False
    if elapsed is not None:
        if model.estimated_minutes:
            is_slow = elapsed > float(model.estimated_minutes) * 2.0
        else:
            is_slow = elapsed > float(get_settings().slow_task_threshold_minutes)

    return {
        "task_id": model.id,
        "started_at": model.started_at.isoformat() if model.started_at else None,
        "completed_at": model.completed_at.isoformat() if model.completed_at else None,
        "estimated_minutes": model.estimated_minutes,
        "actual_minutes": round(elapsed, 1) if elapsed is not None else None,
        "paused_seconds": model.paused_seconds or 0,
        "is_paused": model.last_paused_at is not None,
        "status": model.status,
        "is_slow": is_slow,
    }


@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: str,
    status: str,
    session: AsyncSession = Depends(get_session),
) -> Task:
    """Update a task's status. Records time transitions and auto-advances pipeline.

    Time tracking:
      - in_progress → records started_at (first time) and resumes from pause
      - blocked/review → pauses the timer
      - done → records completed_at and triggers slow-task evolution check
    """
    valid = {s.value for s in TaskStatus}
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    result = await session.execute(
        select(TaskModel).where(TaskModel.id == task_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Task not found")

    now = _utcnow()
    old_status = model.status

    # ── Time tracking logic ───────────────────────────────────────────
    if status == "in_progress" and old_status != "in_progress":
        # Starting or resuming work
        if model.started_at is None:
            model.started_at = now  # first time being worked on
        if model.last_paused_at is not None:
            # Resuming from pause — tally the just-finished pause period
            model.paused_seconds = (model.paused_seconds or 0) + int(
                (now - model.last_paused_at).total_seconds()
            )
            model.last_paused_at = None

    elif status in ("blocked", "review") and old_status in ("in_progress",):
        # Pausing work — only if timer was running
        if model.last_paused_at is None and model.started_at is not None:
            model.last_paused_at = now

    elif status == "done" and old_status != "done":
        # Completing — finalize any active pause
        if model.last_paused_at is not None:
            model.paused_seconds = (model.paused_seconds or 0) + int(
                (now - model.last_paused_at).total_seconds()
            )
            model.last_paused_at = None
        model.completed_at = now

    elif status == "todo" and old_status != "todo":
        # Moving back to todo — close any active pause
        if model.last_paused_at is not None:
            model.paused_seconds = (model.paused_seconds or 0) + int(
                (now - model.last_paused_at).total_seconds()
            )
            model.last_paused_at = None

    # ── Apply status change ───────────────────────────────────────────
    model.status = status
    await session.flush()

    # ── Auto-evolution: check if completed task was slow ──────────────
    if status == "done" and old_status != "done":
        elapsed = _compute_elapsed_minutes(model, now)
        if elapsed is not None:
            await _trigger_evolution_if_slow(session, model, elapsed)

    # ── Auto-advance pipeline when all tasks in the project are done ──
    if status == "done":
        await _auto_advance_if_all_done(session, model.project_id)

    await session.commit()
    await session.refresh(model)
    return _model_to_task(model)


# ── Catch-all: GET /{task_id} (must be last to not shadow /metrics, /{id}/time, /{id}/status) ──


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


# ── Pipeline Auto-Advance (existing, unchanged) ───────────────────────────


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
    pipe_result = await session.execute(
        select(PipelineModel)
        .where(PipelineModel.project_id == project_id)
        .order_by(PipelineModel.created_at.desc())
    )
    pipelines = pipe_result.scalars().all()
    pipeline = next((p for p in pipelines if p.current_phase != "done"), None)
    if pipeline is None:
        from ai_embedded_company.storage.models import ProjectModel
        proj_result = await session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        project = proj_result.scalar_one_or_none()
        if project and project.status == "active":
            project.status = "completed"
        return

    # Advance to next phase
    phase_order = ["idea", "requirements", "design", "implementation", "testing", "deploy", "done"]
    current_idx = phase_order.index(pipeline.current_phase) if pipeline.current_phase in phase_order else 0
    next_idx = min(current_idx + 1, len(phase_order) - 1)
    pipeline.current_phase = phase_order[next_idx]

    # If advancing to "done", also mark the linked idea and project as done
    if phase_order[next_idx] == "done":
        if pipeline.idea_id:
            from ai_embedded_company.storage.models import IdeaModel
            idea_result = await session.execute(
                select(IdeaModel).where(IdeaModel.id == pipeline.idea_id)
            )
            idea = idea_result.scalar_one_or_none()
            if idea and idea.status != "done":
                idea.status = "done"
        from ai_embedded_company.storage.models import ProjectModel
        proj_result = await session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        project = proj_result.scalar_one_or_none()
        if project and project.status == "active":
            project.status = "completed"


# ── Model Conversion ──────────────────────────────────────────────────────


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
        started_at=m.started_at,
        completed_at=m.completed_at,
        paused_seconds=m.paused_seconds or 0,
        last_paused_at=m.last_paused_at,
        estimated_minutes=m.estimated_minutes,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )
