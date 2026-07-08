"""Task failure monitor — watches for failed/timeout tasks and auto-creates
FailureRecord entries to feed the evolution classification pipeline.

This bridges the gap between task execution and the evolution system:
  1. Scans tasks that transitioned to status='failed' or 'timeout'
  2. Detects tasks stuck in 'in_progress' beyond a configurable threshold
  3. Creates structured FailureRecord entries with extracted metadata
  4. Feeds them into the classifier for antibody generation
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage.models import FailureRecord, TaskModel
from ai_embedded_company.evolution.classifier import classify_and_heal

# ── Configuration ──────────────────────────────────────────────────────────

STUCK_TASK_THRESHOLD_MINUTES = 30
"""Tasks in 'in_progress' longer than this are flagged as stalled."""

MAX_PROCESS_TASKS = 100
"""Max tasks to scan per monitor invocation."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _extract_failure_signature(task: TaskModel) -> dict[str, Any]:
    """Extract structured failure metadata from a task for classification."""
    title = task.title or ""
    description = task.description or ""
    combined = f"{title} {description}".lower()

    # Detect failure keywords in task text
    failure_indicators = {
        "timeout": any(kw in combined for kw in ["timeout", "stuck", "hung", "slow", "deadline"]),
        "config": any(kw in combined for kw in ["config", "setting", "env", "path", "not found"]),
        "dependency": any(kw in combined for kw in ["install", "import", "pip", "npm", "missing"]),
        "api": any(kw in combined for kw in ["api", "endpoint", "http", "connection", "request"]),
        "logic": any(kw in combined for kw in ["typeerror", "valueerror", "assert", "invalid"]),
        "resource": any(kw in combined for kw in ["memory", "disk", "quota", "overflow", "oom"]),
    }

    likely_category = "unknown"
    priority_order = ["timeout", "resource", "api", "dependency", "config", "logic"]
    for cat in priority_order:
        if failure_indicators.get(cat):
            likely_category = cat
            break

    return {
        "title": title[:200],
        "likely_category": likely_category,
        "indicators": failure_indicators,
        "description_snippet": description[:500] if description else "(no description)",
        "phase_hint": _detect_phase(title, description),
    }


def _detect_phase(title: str, description: str) -> str:
    """Guess which pipeline phase the failure occurred in."""
    combined = f"{title} {description}".lower()
    phase_keywords: dict[str, list[str]] = {
        "planning": ["plan", "design", "architect", "spec", "requirement"],
        "implementation": ["implement", "write", "code", "build", "develop", "create"],
        "testing": ["test", "verify", "validate", "check", "assert"],
        "deployment": ["deploy", "release", "ci", "cd", "publish"],
        "integration": ["integrate", "connect", "merge", "api", "endpoint"],
    }
    for phase, keywords in phase_keywords.items():
        if any(kw in combined for kw in keywords):
            return phase
    return "unknown"


def _compute_severity(priority: str, is_timeout: bool) -> str:
    """Map task priority + timeout flag to failure severity."""
    if is_timeout:
        return "high"
    severity_map = {"high": "high", "medium": "medium", "low": "low", "critical": "critical"}
    return severity_map.get(priority.lower(), "medium")


async def monitor_task_failures(
    session: AsyncSession,
    *,
    max_tasks: int = MAX_PROCESS_TASKS,
    stuck_threshold_minutes: int = STUCK_TASK_THRESHOLD_MINUTES,
    auto_classify: bool = True,
) -> dict[str, Any]:
    """Scan tasks for failures and create FailureRecord entries.

    Detects two categories:
      1. Tasks with explicit status='failed' or status='timeout'
      2. Tasks stuck 'in_progress' beyond the threshold with no recent activity

    Args:
        session: Database session.
        max_tasks: Max tasks to scan.
        stuck_threshold_minutes: Minutes before an in_progress task is flagged.
        auto_classify: If True, run classifier on newly created records.

    Returns:
        Summary dict with counts and details.
    """
    now = _now()
    cutoff = now - timedelta(minutes=stuck_threshold_minutes)
    stats: dict[str, Any] = {
        "scanned": 0,
        "failed_tasks_found": 0,
        "stuck_tasks_found": 0,
        "failure_records_created": 0,
        "classify_results": None,
        "errors": [],
        "failures_created": [],
    }

    # ── 1. Find explicitly failed tasks ────────────────────────────────────
    failed_stmt = (
        select(TaskModel)
        .where(TaskModel.status.in_(["failed", "timeout"]))
        .limit(max_tasks)
    )
    failed_result = await session.execute(failed_stmt)
    failed_tasks = failed_result.scalars().all()

    stats["failed_tasks_found"] = len(failed_tasks)
    stats["scanned"] += len(failed_tasks)

    # ── 2. Find stuck in_progress tasks ────────────────────────────────────
    stuck_stmt = (
        select(TaskModel)
        .where(
            TaskModel.status == "in_progress",
            TaskModel.started_at.isnot(None),
            TaskModel.started_at < cutoff,
        )
        .limit(max_tasks - len(failed_tasks))
    )
    stuck_result = await session.execute(stuck_stmt)
    stuck_tasks = stuck_result.scalars().all()

    stats["stuck_tasks_found"] = len(stuck_tasks)
    stats["scanned"] += len(stuck_tasks)

    # ── 3. Create FailureRecord for each unmonitored failure ───────────────
    all_candidates = list(failed_tasks) + list(stuck_tasks)
    records_created = 0
    records_ids: list[str] = []

    for task in all_candidates:
        try:
            # Skip if FailureRecord already exists for this task
            existing = await session.execute(
                select(FailureRecord).where(FailureRecord.task_id == task.id)
            )
            if existing.scalar_one_or_none():
                continue

            signature = _extract_failure_signature(task)
            is_timeout = task.status == "timeout" or signature["likely_category"] == "timeout"
            severity = _compute_severity(task.priority, is_timeout)

            record = FailureRecord(
                task_id=task.id,
                project_id=task.project_id,
                agent_role=task.assigned_agent,
                title=f"Task failure: {task.title[:200]}",
                description=(
                    f"Task '{task.title}' (status={task.status}, priority={task.priority}) "
                    f"detected during failure monitoring.\n"
                    f"Phase hint: {signature['phase_hint']}\n"
                    f"Likely category: {signature['likely_category']}\n"
                    f"Description: {signature['description_snippet']}"
                ),
                root_cause=f"Auto-detected from task status={task.status}",
                category=signature["likely_category"],
                severity=severity,
                frequency=1,
                status="reported",
                tags=json.dumps({
                    "source": "task_monitor",
                    "indicators": {k: v for k, v in signature["indicators"].items() if v},
                    "priority": task.priority,
                    "phase_hint": signature["phase_hint"],
                }),
            )
            session.add(record)
            await session.flush()
            records_created += 1
            records_ids.append(record.id)
            stats["failures_created"].append({
                "id": record.id,
                "task_id": task.id,
                "title": task.title[:80],
                "category": signature["likely_category"],
                "status": task.status,
            })

        except Exception as exc:
            stats["errors"].append(f"Task {task.id}: {exc}")

    stats["failure_records_created"] = records_created
    await session.commit()

    # ── 4. Auto-classify newly created records ─────────────────────────────
    if auto_classify and records_ids:
        classify_stats = []
        for rid in records_ids:
            try:
                result = await classify_and_heal(session, record_id=rid)
                classify_stats.append(result)
            except Exception as exc:
                stats["errors"].append(f"Classify {rid}: {exc}")
        stats["classify_results"] = classify_stats

    return stats


async def get_task_failure_summary(
    session: AsyncSession,
) -> dict[str, Any]:
    """Get a summary of task-failure health for dashboard/metrics."""
    now = _now()
    cutoff = now - timedelta(hours=1)

    # Count in_progress tasks started > 1 hour ago (stuck)
    stuck_count = await session.scalar(
        select(TaskModel)
        .where(
            TaskModel.status == "in_progress",
            TaskModel.started_at.isnot(None),
            TaskModel.started_at < cutoff,
        )
        .with_only_columns(TaskModel.id)
    )
    # Just a count query is simpler:
    result = await session.execute(
        select(TaskModel)
        .where(
            TaskModel.status == "in_progress",
            TaskModel.started_at.isnot(None),
            TaskModel.started_at < cutoff,
        )
    )
    stuck_tasks = result.scalars().all()

    failed_count = await session.scalar(
        select(TaskModel)
        .where(TaskModel.status.in_(["failed", "timeout"]))
        .with_only_columns(TaskModel.id)
    )
    result2 = await session.execute(
        select(TaskModel).where(TaskModel.status.in_(["failed", "timeout"]))
    )
    failed_tasks = result2.scalars().all()

    return {
        "stuck_tasks": len(stuck_tasks),
        "failed_tasks": len(failed_tasks),
        "total_monitored_failures": len(stuck_tasks) + len(failed_tasks),
        "stuck_threshold_minutes": STUCK_TASK_THRESHOLD_MINUTES,
    }
