"""Self-evolution API routes — failure alchemy, research loop, knowledge health."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import AntibodyCandidate, FailureRecord, IdeaModel, PipelineModel, ProjectModel, ResearchFinding, TaskModel
from ai_embedded_company.evolution.classifier import classify_and_heal, get_high_frequency_patterns
from ai_embedded_company.evolution.task_monitor import get_task_failure_summary, monitor_task_failures

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Pydantic models for approval flow ──────────────────────────────────────


class ClassificationResult(BaseModel):
    scanned: int = 0
    classified: int = 0
    antibodies_generated: int = 0
    vaccines_generated: int = 0
    candidates_created: int = 0
    by_category: dict[str, int] = {}
    errors: list[str] = []


class CandidateOut(BaseModel):
    id: str
    failure_record_id: str | None = None
    title: str
    category: str
    severity: str
    root_cause: str
    proposed_antibody: str
    proposed_vaccine: str
    proposed_catalyst: str
    confidence_score: float
    status: str
    signature: str
    source: str
    created_at: str | None = None


class ApprovalAction(BaseModel):
    action: str  # "approve" or "reject"
    rejection_reason: str = ""


@router.get("/status")
async def evolution_status(session: AsyncSession = Depends(get_session)) -> dict:
    """Get overall self-evolution health."""
    total_f = (await session.execute(select(func.count(FailureRecord.id)))).scalar() or 0
    analyzed = (await session.execute(
        select(func.count(FailureRecord.id)).where(FailureRecord.status == "analyzed")
    )).scalar() or 0
    high_freq = (await session.execute(
        select(func.count(FailureRecord.id)).where(FailureRecord.frequency >= 3)
    )).scalar() or 0

    cat_result = await session.execute(
        select(FailureRecord.category, func.count(FailureRecord.id)).group_by(FailureRecord.category)
    )
    categories = {row[0]: row[1] for row in cat_result.fetchall()}

    total_r = (await session.execute(select(func.count(ResearchFinding.id)))).scalar() or 0
    accepted = (await session.execute(
        select(func.count(ResearchFinding.id)).where(ResearchFinding.status == "accepted")
    )).scalar() or 0

    return {
        "failures": {
            "total": total_f, "analyzed": analyzed, "high_frequency_patterns": high_freq,
            "by_category": categories,
            "antibodies_active": analyzed,
            "vaccines_active": high_freq,
        },
        "research": {
            "total_findings": total_r, "accepted": accepted,
            "conversion_rate": f"{int(accepted / total_r * 100)}%" if total_r > 0 else "0%",
        },
        "evolution_health": "healthy" if analyzed > 0 else "nascent",
    }


@router.get("/failures")
async def list_failures(
    category: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List failure records with optional filters."""
    stmt = select(FailureRecord)
    if category:
        stmt = stmt.where(FailureRecord.category == category)
    if severity:
        stmt = stmt.where(FailureRecord.severity == severity)
    if status:
        stmt = stmt.where(FailureRecord.status == status)
    stmt = stmt.order_by(FailureRecord.frequency.desc()).limit(limit)
    result = await session.execute(stmt)
    return [
        {
            "id": r.id, "title": r.title, "category": r.category, "severity": r.severity,
            "frequency": r.frequency, "status": r.status,
            "root_cause": r.root_cause[:200] if r.root_cause else None,
            "antibody": r.antibody[:300] if r.antibody else None,
            "vaccine": r.vaccine[:300] if r.vaccine else None,
            "catalyst": r.catalyst[:300] if r.catalyst else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in result.scalars().all()
    ]


@router.get("/recommend")
async def evolution_recommend(session: AsyncSession = Depends(get_session)) -> dict:
    """Analyze past performance and recommend next actions for the evolution system.

    Looks at idea → pipeline → completion conversion rates, failure patterns,
    and throughput data to suggest what to focus on next.
    """
    # ── Idea conversion analysis ─────────────────────────────────────
    idea_result = await session.execute(select(IdeaModel))
    ideas = idea_result.scalars().all()
    total_ideas = len(ideas)
    done_ideas = [i for i in ideas if i.status == "done"]
    in_progress_ideas = [i for i in ideas if i.status == "in_progress"]
    refining_ideas = [i for i in ideas if i.status == "refining"]

    # Count by suggested pipeline type
    pipeline_type_success: dict[str, dict] = {}
    for idea in ideas:
        ptype = idea.suggested_pipeline or "unknown"
        if ptype not in pipeline_type_success:
            pipeline_type_success[ptype] = {
                "total": 0, "done": 0, "in_progress": 0, "refining": 0,
            }
        pipeline_type_success[ptype]["total"] += 1
        if idea.status == "done":
            pipeline_type_success[ptype]["done"] += 1
        elif idea.status == "in_progress":
            pipeline_type_success[ptype]["in_progress"] += 1
        elif idea.status == "refining":
            pipeline_type_success[ptype]["refining"] += 1

    # Add conversion rates
    for ptype, data in pipeline_type_success.items():
        data["conversion_rate"] = (
            round(data["done"] / data["total"] * 100, 1) if data["total"] > 0 else 0.0
        )

    # ── Failure pattern analysis ─────────────────────────────────────
    fail_result = await session.execute(
        select(FailureRecord).order_by(FailureRecord.frequency.desc()).limit(10)
    )
    top_failures = fail_result.scalars().all()
    failure_patterns = [
        {
            "category": f.category,
            "frequency": f.frequency,
            "severity": f.severity,
            "antibody": f.antibody[:200] if f.antibody else None,
        }
        for f in top_failures
    ]

    # ── Task throughput ──────────────────────────────────────────────
    task_result = await session.execute(select(TaskModel))
    tasks = task_result.scalars().all()
    total_tasks = len(tasks)
    done_tasks = [t for t in tasks if t.status == "done"]
    avg_cycle_minutes = 0.0
    if done_tasks:
        times = []
        for t in done_tasks:
            if t.started_at and t.completed_at:
                start = t.started_at
                end = t.completed_at
                # Make both offset-aware if one is naive
                if start.tzinfo is None and end.tzinfo is not None:
                    start = start.replace(tzinfo=end.tzinfo)
                elif end.tzinfo is None and start.tzinfo is not None:
                    end = end.replace(tzinfo=start.tzinfo)
                elapsed = (end - start).total_seconds() / 60.0
                times.append(elapsed)
        avg_cycle_minutes = round(sum(times) / len(times), 1) if times else 0.0

    # ── Pipeline throughput ──────────────────────────────────────────
    pipe_result = await session.execute(select(PipelineModel))
    pipelines = pipe_result.scalars().all()
    done_pipelines = [p for p in pipelines if p.current_phase == "done"]
    active_pipelines = [p for p in pipelines if p.current_phase != "done"]

    # ── Generate recommendation ──────────────────────────────────────
    recommendation: dict = {
        "focus_area": None,
        "suggested_idea_type": None,
        "suggested_pipeline": None,
        "reasoning": [],
    }

    if not ideas:
        recommendation["focus_area"] = "seed-ideas"
        recommendation["reasoning"].append(
            "No ideas exist yet — start by capturing initial ideas to seed the pipeline."
        )
    elif not done_ideas and in_progress_ideas:
        recommendation["focus_area"] = "complete-in-progress"
        recommendation["reasoning"].append(
            f"{len(in_progress_ideas)} ideas are in progress but none completed — "
            "focus on driving existing ideas to completion before adding new ones."
        )
    elif pipeline_type_success:
        # Find the best-converting pipeline type
        best_type = max(
            pipeline_type_success.items(),
            key=lambda kv: kv[1]["conversion_rate"],
        )
        recommendation["suggested_idea_type"] = best_type[0]
        recommendation["suggested_pipeline"] = best_type[0]
        recommendation["reasoning"].append(
            f"Pipeline type '{best_type[0]}' has the highest conversion rate "
            f"({best_type[1]['conversion_rate']}%) with {best_type[1]['done']} completed ideas."
        )

    if top_failures:
        top_cat = top_failures[0].category or "uncategorized"
        recommendation["reasoning"].append(
            f"Most frequent failure category: '{top_cat}' "
            f"(appeared {top_failures[0].frequency}x). "
            f"Antibody: {top_failures[0].antibody or 'not yet generated'}."
        )

    recommendation["reasoning"].append(
        f"System throughput: {avg_cycle_minutes} min avg task cycle, "
        f"{len(done_pipelines)}/{len(pipelines)} pipelines completed, "
        f"{len(done_tasks)}/{total_tasks} tasks done."
    )

    return {
        "summary": {
            "total_ideas": total_ideas,
            "done_ideas": len(done_ideas),
            "in_progress_ideas": len(in_progress_ideas),
            "refining_ideas": len(refining_ideas),
            "total_pipelines": len(pipelines),
            "done_pipelines": len(done_pipelines),
            "active_pipelines": len(active_pipelines),
            "total_tasks": total_tasks,
            "done_tasks": len(done_tasks),
            "average_task_cycle_minutes": avg_cycle_minutes,
        },
        "pipeline_type_performance": pipeline_type_success,
        "top_failure_patterns": failure_patterns,
        "recommendation": recommendation,
    }


@router.get("/research")
async def list_research(
    status: str | None = None,
    source_type: str | None = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List research findings with optional filters for status, type, and date range."""
    stmt = select(ResearchFinding)
    if status:
        stmt = stmt.where(ResearchFinding.status == status)
    if source_type:
        stmt = stmt.where(ResearchFinding.source_type == source_type)
    stmt = stmt.order_by(ResearchFinding.relevance_score.desc()).limit(limit)
    result = await session.execute(stmt)
    return [
        {
            "id": f.id, "title": f.title, "source": f.source,
            "source_type": f.source_type, "summary": f.summary,
            "relevance_score": f.relevance_score, "status": f.status,
            "debate_notes": f.debate_notes[:300] if f.debate_notes else None,
            "action_items": f.action_items, "idea_id": f.idea_id,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in result.scalars().all()
    ]


# ── Auto-classification & Approval Flow ────────────────────────────────────


@router.post("/classify")
async def auto_classify_failures(
    record_id: str | None = Query(None, description="Optional — classify a specific record by ID"),
    max_records: int = Query(50, description="Max records to process"),
    session: AsyncSession = Depends(get_session),
) -> ClassificationResult:
    """Scan unclassified (status='reported') failure records, auto-classify them,
    and create antibody candidates for human approval.

    This is the core of the detection-to-antibody loop. Instead of directly writing
    antibodies/vaccines to FailureRecords, it creates AntibodyCandidates that
    await explicit human approval before activation.
    """
    now = _utcnow()
    result = ClassificationResult()

    # 1. Run the existing classifier
    classify_stats = await classify_and_heal(session, record_id=record_id, max_records=max_records)
    result.scanned = classify_stats.get("scanned", 0)
    result.classified = classify_stats.get("classified", 0)
    result.antibodies_generated = classify_stats.get("antibodies_generated", 0)
    result.vaccines_generated = classify_stats.get("vaccines_generated", 0)
    result.by_category = classify_stats.get("by_category", {})
    result.errors = classify_stats.get("errors", [])

    # 2. Find newly analyzed records and create antibody candidates for approval
    stmt = select(FailureRecord).where(
        FailureRecord.status == "analyzed",
        FailureRecord.antibody != "",
    )
    if record_id:
        stmt = stmt.where(FailureRecord.id == record_id)
    stmt = stmt.order_by(FailureRecord.updated_at.desc()).limit(max_records)

    analyzed = (await session.execute(stmt)).scalars().all()

    for record in analyzed:
        # Skip if a candidate already exists for this failure record
        existing = await session.execute(
            select(AntibodyCandidate).where(
                AntibodyCandidate.failure_record_id == record.id,
                AntibodyCandidate.status == "pending",
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Build a signature for deduplication
        signature = f"{record.category}:{record.agent_role or 'none'}:{record.title[:80]}"

        # Check for duplicate by signature
        dup = await session.execute(
            select(AntibodyCandidate).where(
                AntibodyCandidate.signature == signature,
                AntibodyCandidate.status.in_(["pending", "approved"]),
            )
        )
        if dup.scalar_one_or_none():
            continue

        # Calculate confidence score based on keyword match density
        total_keywords = sum(
            len(config["keywords"]) for config in [
                {"keywords": ["config", "setting", "env", "environment", "variable",
                              "path", "not found", "no such file", "permission"]},
                {"keywords": ["import", "module", "package", "library", "dependency",
                              "install", "pip", "npm", "missing", "not installed"]},
                {"keywords": ["typeerror", "valueerror", "keyerror", "indexerror",
                              "attributeerror", "assertion", "unexpected", "invalid"]},
                {"keywords": ["phase", "step", "pipeline", "sequence", "ordering",
                              "missing step", "advance", "transition"]},
                {"keywords": ["memory", "oom", "out of memory", "disk", "space",
                              "quota", "rate limit", "timeout", "connection refused",
                              "too many", "overflow"]},
                {"keywords": ["api", "endpoint", "http", "status code", "4xx",
                              "5xx", "response", "request failed", "unreachable"]},
                {"keywords": ["timeout", "slow", "took too long", "exceeded",
                              "threshold", "hung", "stall", "deadline"]},
                {"keywords": ["auth", "authorization", "authentication", "token",
                              "credential", "ssl", "tls", "encrypt", "permission denied"]},
            ]
        )
        confidence = min(1.0, max(0.3, record.frequency / 5.0)) if total_keywords > 0 else 0.5

        candidate = AntibodyCandidate(
            id=str(uuid.uuid4()),
            failure_record_id=record.id,
            title=record.title,
            category=record.category,
            severity=record.severity,
            root_cause=record.root_cause[:500] if record.root_cause else "",
            proposed_antibody=record.antibody,
            proposed_vaccine=record.vaccine or "",
            proposed_catalyst=record.catalyst or "",
            confidence_score=round(confidence, 2),
            status="pending",
            source="auto-classify",
            signature=signature,
        )
        session.add(candidate)
        result.candidates_created += 1

    await session.commit()
    return result


@router.get("/antibody-candidates")
async def list_antibody_candidates(
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    limit: int = Query(50, description="Max results"),
    session: AsyncSession = Depends(get_session),
) -> list[CandidateOut]:
    """List antibody candidates awaiting or after human approval."""
    stmt = select(AntibodyCandidate).order_by(AntibodyCandidate.created_at.desc())
    if status:
        stmt = stmt.where(AntibodyCandidate.status == status)
    stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    candidates = result.scalars().all()

    return [
        CandidateOut(
            id=c.id,
            failure_record_id=c.failure_record_id,
            title=c.title,
            category=c.category,
            severity=c.severity,
            root_cause=c.root_cause[:300] if c.root_cause else "",
            proposed_antibody=c.proposed_antibody,
            proposed_vaccine=c.proposed_vaccine,
            proposed_catalyst=c.proposed_catalyst,
            confidence_score=c.confidence_score,
            status=c.status,
            signature=c.signature,
            source=c.source,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in candidates
    ]


class MonitorResult(BaseModel):
    scanned: int = 0
    failed_tasks_found: int = 0
    stuck_tasks_found: int = 0
    failure_records_created: int = 0
    errors: list[str] = []


@router.post("/monitor")
async def monitor_task_failures_endpoint(
    max_tasks: int = Query(100, description="Max tasks to scan"),
    stuck_threshold_minutes: int = Query(30, description="Minutes before in_progress task is flagged as stuck"),
    session: AsyncSession = Depends(get_session),
) -> MonitorResult:
    """Scan tasks for failures/timeouts and auto-create classified FailureRecords.

    This closes the detection-to-antibody loop by bridging task execution
    status changes to the evolution classification pipeline.
    """
    raw = await monitor_task_failures(
        session,
        max_tasks=max_tasks,
        stuck_threshold_minutes=stuck_threshold_minutes,
        auto_classify=True,
    )
    return MonitorResult(
        scanned=raw.get("scanned", 0),
        failed_tasks_found=raw.get("failed_tasks_found", 0),
        stuck_tasks_found=raw.get("stuck_tasks_found", 0),
        failure_records_created=raw.get("failure_records_created", 0),
        errors=raw.get("errors", []),
    )


@router.post("/antibody-candidates/{candidate_id}/review")
async def review_antibody_candidate(
    candidate_id: str,
    action: ApprovalAction,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Approve or reject an antibody candidate.

    - 'approve': activates the antibody/vaccine/catalyst on the linked FailureRecord.
    - 'reject': marks the candidate as rejected with an optional reason.
    """
    result = await session.execute(
        select(AntibodyCandidate).where(AntibodyCandidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    now = _utcnow()

    if action.action == "approve":
        # Activate the antibody on the linked FailureRecord
        if candidate.failure_record_id:
            fr_result = await session.execute(
                select(FailureRecord).where(FailureRecord.id == candidate.failure_record_id)
            )
            record = fr_result.scalar_one_or_none()
            if record:
                record.antibody = candidate.proposed_antibody
                record.vaccine = candidate.proposed_vaccine
                record.catalyst = candidate.proposed_catalyst or record.catalyst
                record.status = "analyzed"
                record.updated_at = now

        candidate.status = "approved"
        candidate.approved_at = now
        await session.commit()

        return {
            "status": "approved",
            "candidate_id": candidate_id,
            "message": f"Antibody '{candidate.title[:60]}' approved and activated.",
        }

    elif action.action == "reject":
        candidate.status = "rejected"
        candidate.rejection_reason = action.rejection_reason
        await session.commit()

        return {
            "status": "rejected",
            "candidate_id": candidate_id,
            "message": f"Antibody '{candidate.title[:60]}' rejected.",
            "rejection_reason": action.rejection_reason,
        }

    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
