"""Failure classification engine — auto-detect, classify, and generate
antibodies from task timeouts and execution failures.

This closes the detection-to-antibody loop:
  1. Scan unclassified FailureRecords (status='reported')
  2. Extract error signatures from task metadata
  3. Classify into evolution schema categories
  4. Generate antibody (prevention) and vaccine (pre-task warning) candidates
  5. Update records and surface high-frequency patterns

Watchdog: tracks consecutive classification errors and circuit-breaks
when the error rate exceeds a configurable threshold.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage.models import FailureRecord, TaskModel

# ── Sentinel for circuit breaker ──────────────────────────────────────────────

class CircuitBreakerOpenError(RuntimeError):
    """Raised when the classifier watchdog circuit breaker is open — too
    many consecutive failures have occurred. Manual reset or cooldown required."""


# ── Watchdog / Circuit Breaker ─────────────────────────────────────────────────

_WATCHDOG_STATE: dict[str, Any] = {
    "consecutive_errors": 0,
    "total_errors": 0,
    "total_processed": 0,
    "last_error_at": None,
    "circuit_open": False,
    "circuit_open_since": None,
    "max_consecutive_errors": 5,
}


def reset_watchdog(max_consecutive_errors: int = 5) -> None:
    """Reset the classifier watchdog state (e.g. after manual intervention)."""
    _WATCHDOG_STATE["consecutive_errors"] = 0
    _WATCHDOG_STATE["total_errors"] = 0
    _WATCHDOG_STATE["total_processed"] = 0
    _WATCHDOG_STATE["last_error_at"] = None
    _WATCHDOG_STATE["circuit_open"] = False
    _WATCHDOG_STATE["circuit_open_since"] = None
    _WATCHDOG_STATE["max_consecutive_errors"] = max_consecutive_errors


def get_watchdog_state() -> dict[str, Any]:
    """Return a snapshot of the current watchdog / circuit breaker state."""
    return dict(_WATCHDOG_STATE)


def _record_success() -> None:
    _WATCHDOG_STATE["consecutive_errors"] = 0
    _WATCHDOG_STATE["total_processed"] += 1


def _record_error() -> None:
    now = datetime.now(timezone.utc)
    _WATCHDOG_STATE["consecutive_errors"] += 1
    _WATCHDOG_STATE["total_errors"] += 1
    _WATCHDOG_STATE["total_processed"] += 1
    _WATCHDOG_STATE["last_error_at"] = now
    if _WATCHDOG_STATE["consecutive_errors"] >= _WATCHDOG_STATE["max_consecutive_errors"]:
        _WATCHDOG_STATE["circuit_open"] = True
        _WATCHDOG_STATE["circuit_open_since"] = now


def _check_circuit_breaker() -> None:
    """Raise CircuitBreakerOpenError if the circuit is open."""
    if _WATCHDOG_STATE["circuit_open"]:
        raise CircuitBreakerOpenError(
            f"Classifier circuit breaker is open after "
            f"{_WATCHDOG_STATE['consecutive_errors']} consecutive errors (threshold: "
            f"{_WATCHDOG_STATE['max_consecutive_errors']}). "
            f"Call reset_watchdog() after manual intervention."
        )

# ── Failure category definitions ──────────────────────────────────────────────

FAILURE_CATEGORIES = {
    "config_miss": {
        "keywords": ["config", "setting", "env", "environment", "variable",
                      "path", "not found", "no such file", "permission"],
        "description": "Missing or incorrect configuration",
        "severity": "medium",
    },
    "dependency": {
        "keywords": ["import", "module", "package", "library", "dependency",
                      "install", "pip", "npm", "missing", "not installed"],
        "description": "Missing or incompatible dependency",
        "severity": "medium",
    },
    "logic_error": {
        "keywords": ["typeerror", "valueerror", "keyerror", "indexerror",
                      "attributeerror", "assertion", "unexpected", "invalid"],
        "description": "Application logic or coding error",
        "severity": "high",
    },
    "pipeline": {
        "keywords": ["phase", "step", "pipeline", "sequence", "ordering",
                      "missing step", "advance", "transition"],
        "description": "Pipeline configuration or ordering issue",
        "severity": "medium",
    },
    "resource": {
        "keywords": ["memory", "oom", "out of memory", "disk", "space",
                      "quota", "rate limit", "timeout", "connection refused",
                      "too many", "overflow"],
        "description": "Resource exhaustion or contention",
        "severity": "high",
    },
    "api_error": {
        "keywords": ["api", "endpoint", "http", "status code", "4xx",
                      "5xx", "response", "request failed", "unreachable"],
        "description": "API or external service error",
        "severity": "medium",
    },
    "timeout": {
        "keywords": ["timeout", "slow", "took too long", "exceeded",
                      "threshold", "hung", "stall", "deadline"],
        "description": "Task exceeded expected completion time",
        "severity": "low",
    },
    "security": {
        "keywords": ["auth", "authorization", "authentication", "token",
                      "credential", "ssl", "tls", "encrypt", "permission denied"],
        "description": "Security or access control issue",
        "severity": "critical",
    },
}

CATEGORY_ORDER = [
    "config_miss", "dependency", "logic_error", "pipeline",
    "resource", "api_error", "timeout", "security",
]

# ── Antibody templates ────────────────────────────────────────────────────────

ANTIBODY_TEMPLATES: dict[str, str] = {
    "config_miss": (
        "Before starting tasks, verify that all required configuration files, "
        "environment variables, and path settings exist and are correct. "
        "Add a pre-flight config validation step."
    ),
    "dependency": (
        "Run `uv sync` (or equivalent) before task execution and verify that "
        "all required packages are installed and importable. Pin dependency versions."
    ),
    "logic_error": (
        "Add input validation and type checking at function boundaries. "
        "Use exhaustive pattern matching and handle all edge cases explicitly."
    ),
    "pipeline": (
        "Verify pipeline phase ordering before advancing. Ensure all prerequisites "
        "of the next phase are complete before transitioning."
    ),
    "resource": (
        "Set explicit resource limits and monitor usage during execution. "
        "Implement backpressure and circuit-breaker patterns for rate-limited resources."
    ),
    "api_error": (
        "Implement retry with exponential backoff for all external API calls. "
        "Add fallback responses and circuit-breaker for unreliable endpoints."
    ),
    "timeout": (
        "Set explicit time budgets for each task phase. Monitor elapsed time "
        "and alert when approaching the threshold. Break long tasks into smaller units."
    ),
    "security": (
        "Validate all credentials and tokens before use. Check permissions early "
        "and provide meaningful error messages for access failures."
    ),
}

VACCINE_TEMPLATES: dict[str, str] = {
    "config_miss": (
        "⚠️ This task type has a history of config_miss failures. "
        "Verify all configuration files, env vars, and paths before proceeding."
    ),
    "dependency": (
        "⚠️ Similar tasks have failed due to missing dependencies. "
        "Run package installation and verify imports before starting."
    ),
    "logic_error": (
        "⚠️ Logic errors are common in this category. "
        "Add defensive checks and handle None/empty cases explicitly."
    ),
    "pipeline": (
        "⚠️ Pipeline ordering failures have been recorded. "
        "Verify that all prerequisite phases are complete before advancing."
    ),
    "resource": (
        "⚠️ Resource exhaustion has occurred in similar tasks. "
        "Monitor memory/disk/rate-limit usage and add backpressure handling."
    ),
    "api_error": (
        "⚠️ External API failures have been detected. "
        "Ensure retry logic and fallback handlers are in place."
    ),
    "timeout": (
        "⚠️ Timeout failures are frequent in this area. "
        "Set explicit time budgets and consider splitting the task."
    ),
    "security": (
        "⚠️ Security-related failures have been recorded. "
        "Validate credentials, tokens, and permissions before starting."
    ),
}

# ── Classification logic ─────────────────────────────────────────────────────


def _current_timestamp() -> datetime:
    return datetime.now(timezone.utc)


# ── Input validation helpers ──────────────────────────────────────────────────

_KNOWN_CATEGORIES: set[str] = set(FAILURE_CATEGORIES.keys())


def validate_record(record: FailureRecord) -> list[str]:
    """Validate a failure record's fields. Returns a list of issues (empty = valid)."""
    issues: list[str] = []
    if not record.title and not record.description and not record.root_cause:
        issues.append("Record has no title, description, or root_cause — insufficient data")
    if record.status not in ("reported", "analyzed", "resolved"):
        issues.append(f"Unknown status: {record.status}")
    if record.severity not in ("low", "medium", "high", "critical"):
        issues.append(f"Unknown severity: {record.severity}")
    if record.category and record.category not in _KNOWN_CATEGORIES:
        issues.append(f"Unknown category: {record.category}")
    return issues


def _classify_failure(record: FailureRecord) -> str | None:
    """Heuristically classify a failure record into a category.

    Examines title, description, and root_cause text against keyword
    patterns for each failure category. Returns the best-matching category
    or None if no match found.

    Input validation: returns None for records with empty title AND description.
    """
    title = (record.title or "").strip()
    description = (record.description or "").strip()
    root_cause = (record.root_cause or "").strip()

    if not title and not description and not root_cause:
        return None  # Insufficient data to classify

    text = " ".join([title, description, root_cause]).lower()

    scores: dict[str, int] = {}
    for cat, config in FAILURE_CATEGORIES.items():
        score = 0
        for keyword in config["keywords"]:
            count = text.count(keyword.lower())
            score += count

        if score > 0:
            # Normalise by keyword count to avoid category-length bias
            n_keywords = max(len(config["keywords"]), 1)
            scores[cat] = score / n_keywords

    if not scores:
        return None

    # Return highest-scoring category (ties broken by category order)
    best = max(
        CATEGORY_ORDER,
        key=lambda k: scores.get(k, 0),
    )
    return best


def _generate_antibody(category: str, record: FailureRecord) -> str:
    """Generate an antibody (prevention strategy) for a classified failure."""
    template = ANTIBODY_TEMPLATES.get(category, "")
    if not template:
        # Generic template for uncategorized failures
        template = (
            "Investigate and document the root cause. Add monitoring and "
            "alerting for this failure pattern to prevent recurrence."
        )

    # Customize based on specific task context
    context_parts: list[str] = []
    if record.agent_role:
        context_parts.append(f"agent: {record.agent_role}")
    if record.task_id:
        context_parts.append(f"task: {record.title[:40]}...")

    context = " | ".join(context_parts)
    return f"[{context}] {template}" if context else template


def _generate_vaccine(category: str) -> str:
    """Generate a vaccine (pre-task warning) for a failure category."""
    return VACCINE_TEMPLATES.get(category, (
        "⚠️ Similar tasks have encountered failures. "
        "Review recent failure records for this category before proceeding."
    ))


# ── Public API ────────────────────────────────────────────────────────────────


async def classify_and_heal(
    session: AsyncSession,
    record_id: str | None = None,
    max_records: int = 50,
) -> dict[str, Any]:
    """Scan unclassified FailureRecords, classify them, and generate antibodies.

    Args:
        session: Database session.
        record_id: Optional — classify a specific record by ID.
        max_records: Maximum records to process (default 50).

    Returns:
        Summary dict with counts of classified, updated, and skipped records.
    """
    now = _current_timestamp()
    stats: dict[str, Any] = {
        "scanned": 0,
        "classified": 0,
        "updated": 0,
        "antibodies_generated": 0,
        "vaccines_generated": 0,
        "by_category": {},
        "errors": [],
    }

    # ── Circuit breaker check ───────────────────────────────────────────
    try:
        _check_circuit_breaker()
    except CircuitBreakerOpenError:
        stats["errors"].append(
            "Circuit breaker is open — refusing to classify. "
            "Call reset_watchdog() after manual intervention."
        )
        return stats

    # Build the query
    stmt = select(FailureRecord)
    if record_id:
        stmt = stmt.where(FailureRecord.id == record_id)
    else:
        stmt = stmt.where(
            FailureRecord.status.in_(["reported"])
        )
    stmt = stmt.order_by(FailureRecord.created_at.asc()).limit(max_records)

    result = await session.execute(stmt)
    records = result.scalars().all()

    stats["scanned"] = len(records)

    for record in records:
        try:
            # ── Validate input ───────────────────────────────────────────
            issues = validate_record(record)
            if issues:
                if not record.title and not record.description and not record.root_cause:
                    # Skip records with no usable data
                    stats["errors"].append(
                        f"Record {record.id}: skip — empty title, description, and root_cause"
                    )
                    _record_success()  # Not an error, just a skip
                    continue
                stats["errors"].append(
                    f"Record {record.id}: validation issues: {'; '.join(issues)}"
                )

            # 1. Classify
            old_category = record.category
            new_category = _classify_failure(record)

            if new_category and new_category != old_category:
                record.category = new_category
                stats["classified"] += 1

            # 2. Generate antibody if missing
            if not record.antibody and new_category:
                record.antibody = _generate_antibody(new_category, record)
                record.vaccine = _generate_vaccine(new_category)
                stats["antibodies_generated"] += 1
                stats["vaccines_generated"] += 1

            # 3. Determine severity based on category
            cat_config = FAILURE_CATEGORIES.get(new_category or "unknown", {})
            suggested_severity = cat_config.get("severity", "medium")
            if record.severity == "medium" and suggested_severity != "medium":
                record.severity = suggested_severity

            # 4. Mark as analyzed
            if record.status == "reported":
                record.status = "analyzed"
                stats["by_category"][new_category or "unknown"] = \
                    stats["by_category"].get(new_category or "unknown", 0) + 1

            record.updated_at = now
            stats["updated"] += 1
            _record_success()

        except Exception as exc:
            _record_error()
            stats["errors"].append(f"Record {record.id}: {exc}")

    await session.commit()

    return stats


async def get_high_frequency_patterns(
    session: AsyncSession,
    min_frequency: int = 2,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Find high-frequency failure patterns for antibody reinforcement."""
    result = await session.execute(
        select(FailureRecord)
        .where(FailureRecord.frequency >= min_frequency)
        .order_by(FailureRecord.frequency.desc())
        .limit(limit)
    )
    records = result.scalars().all()

    return [
        {
            "id": r.id,
            "category": r.category,
            "frequency": r.frequency,
            "severity": r.severity,
            "title": r.title,
            "antibody": r.antibody[:200] if r.antibody else None,
            "vaccine": r.vaccine[:200] if r.vaccine else None,
            "status": r.status,
        }
        for r in records
    ]


async def reclassify_all(
    session: AsyncSession,
) -> dict[str, Any]:
    """Re-classify ALL failure records, regardless of current status."""
    result = await session.execute(
        select(FailureRecord).order_by(FailureRecord.created_at.asc())
    )
    records = result.scalars().all()

    stats: dict[str, Any] = {
        "scanned": len(records),
        "category_changes": 0,
        "antibodies_added": 0,
        "vaccines_added": 0,
        "by_category": {},
    }

    for record in records:
        new_category = _classify_failure(record)
        if new_category and new_category != record.category:
            record.category = new_category
            stats["category_changes"] += 1

        if not record.antibody and new_category:
            record.antibody = _generate_antibody(new_category, record)
            record.vaccine = _generate_vaccine(new_category)
            stats["antibodies_added"] += 1
            stats["vaccines_added"] += 1

        stats["by_category"][record.category or "unknown"] = \
            stats["by_category"].get(record.category or "unknown", 0) + 1

        record.updated_at = _current_timestamp()

    await session.commit()
    return stats
