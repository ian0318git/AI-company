"""Dashboard aggregation endpoint — combines metrics from across the system
into a single response for the Autonomous Cycle Health Dashboard."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import (
    FailureRecord,
    IdeaModel,
    PipelineModel,
    ProjectModel,
    TaskModel,
)

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _naive(dt: datetime | None) -> datetime | None:
    """Strip timezone info for SQLite-safe comparisons/arithmetic."""
    return dt.replace(tzinfo=None) if dt else None


@router.get("/metrics")
async def dashboard_metrics(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Aggregated metrics for the health dashboard — one call, all data."""
    now = _utcnow()

    # ── Pipeline funnel ──────────────────────────────────────────────
    pipe_result = await session.execute(select(PipelineModel))
    pipelines = pipe_result.scalars().all()
    total_pipelines = len(pipelines)

    phase_counts: dict[str, int] = {}
    pipeline_type_counts: dict[str, int] = {}
    for p in pipelines:
        phase = p.current_phase or "unknown"
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

        ptype = p.pipeline_type or "unknown"
        pipeline_type_counts[ptype] = pipeline_type_counts.get(ptype, 0) + 1

    # ── Idea funnel ──────────────────────────────────────────────────
    idea_result = await session.execute(select(IdeaModel))
    ideas = idea_result.scalars().all()
    total_ideas = len(ideas)
    idea_status_counts: dict[str, int] = {}
    for idea in ideas:
        s = idea.status or "new"
        idea_status_counts[s] = idea_status_counts.get(s, 0) + 1

    # ── Task metrics ─────────────────────────────────────────────────
    task_result = await session.execute(select(TaskModel))
    tasks = task_result.scalars().all()
    total_tasks = len(tasks)

    task_status_counts: dict[str, int] = {}
    total_tokens = 0
    completed_count = 0
    completed_minutes = 0.0
    tasks_tracked = 0
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_minutes = 0.0

    for t in tasks:
        s = t.status or "todo"
        task_status_counts[s] = task_status_counts.get(s, 0) + 1

        tokens = t.tokens_used or 0
        total_tokens += tokens

        sa = _naive(t.started_at)
        ca = _naive(t.completed_at)

        if sa:
            tasks_tracked += 1

        if t.status == "done" and sa and ca:
            elapsed = (ca - sa).total_seconds() / 60.0
            completed_minutes += elapsed
            completed_count += 1

        # Minutes logged today
        if sa and sa >= today_start:
            today_minutes += _task_elapsed_minutes(t, now)
        elif ca and ca >= today_start and not sa:
            today_minutes += _task_elapsed_minutes(t, now)

    avg_completion_minutes = (
        round(completed_minutes / completed_count, 1) if completed_count > 0 else None
    )

    # ── Project stats ────────────────────────────────────────────────
    proj_result = await session.execute(select(ProjectModel))
    projects = proj_result.scalars().all()
    active_projects = sum(1 for p in projects if p.status == "active")

    # ── Evolution health ─────────────────────────────────────────────
    fail_result = await session.execute(select(FailureRecord))
    failures = fail_result.scalars().all()
    total_failures = len(failures)

    failure_categories: dict[str, int] = {}
    failure_severities: dict[str, int] = {}
    for f in failures:
        cat = f.category or "uncategorized"
        failure_categories[cat] = failure_categories.get(cat, 0) + 1
        sev = f.severity or "unknown"
        failure_severities[sev] = failure_severities.get(sev, 0) + 1

    # ── Cycle throughput: ideas created per day ──────────────────────
    idea_daily: dict[str, int] = {}
    for idea in ideas:
        day = idea.created_at.strftime("%Y-%m-%d")
        idea_daily[day] = idea_daily.get(day, 0) + 1

    pipeline_daily: dict[str, int] = {}
    for p in pipelines:
        day = p.created_at.strftime("%Y-%m-%d")
        pipeline_daily[day] = pipeline_daily.get(day, 0) + 1

    return {
        "pipelines": {
            "total": total_pipelines,
            "by_phase": phase_counts,
            "by_type": pipeline_type_counts,
        },
        "ideas": {
            "total": total_ideas,
            "by_status": idea_status_counts,
            "daily_created": idea_daily,
        },
        "tasks": {
            "total": total_tasks,
            "tracked": tasks_tracked,
            "by_status": task_status_counts,
            "today_minutes": round(today_minutes, 1),
            "completed_count": completed_count,
            "average_completion_minutes": avg_completion_minutes,
            "total_tokens": total_tokens,
        },
        "projects": {
            "total": len(projects),
            "active": active_projects,
        },
        "evolution": {
            "total_failures": total_failures,
            "by_category": failure_categories,
            "by_severity": failure_severities,
            "antibodies": sum(1 for f in failures if f.antibody and f.antibody.strip()),
            "vaccines": sum(1 for f in failures if f.vaccine and f.vaccine.strip()),
        },
        "cycle_throughput": {
            "ideas_per_day": idea_daily,
            "pipelines_per_day": pipeline_daily,
        },
    }


def _task_elapsed_minutes(task: TaskModel, now: datetime) -> float:
    """Compute elapsed minutes for a task (all datetimes normalized to naive)."""
    sa = _naive(task.started_at)
    ca = _naive(task.completed_at)
    if task.status == "done" and ca and sa:
        return (ca - sa).total_seconds() / 60.0
    if sa:
        paused = task.paused_seconds or 0
        raw = (now - sa).total_seconds() - paused
        return max(raw, 0) / 60.0
    return 0.0
