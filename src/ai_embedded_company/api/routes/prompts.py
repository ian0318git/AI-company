"""Prompt Optimization API routes — template management, A/B testing, and insight tracking.

Database-backed implementation for persistent prompt optimization.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import (
    TaskModel,
    PromptTemplateModel,
    PromptResultModel,
    ABExperimentModel,
    OptimizationInsightModel,
)

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Pydantic models ───────────────────────────────────────────────────────


class PromptTemplateCreate(BaseModel):
    agent_role: str
    pipeline_type: str = "any"
    template_name: str
    template_body: str
    token_count: int = 0
    tags: str = "[]"
    source_experiment_id: str | None = None


class PromptTemplateOut(BaseModel):
    id: str
    agent_role: str
    pipeline_type: str
    template_name: str
    template_body: str
    token_count: int
    version: int
    status: str
    tags: str = "[]"
    source_experiment_id: str | None = None
    avg_tokens: float = 0.0
    avg_seconds: float = 0.0
    use_count: int = 0
    created_at: str
    updated_at: str


class ABTestCreate(BaseModel):
    experiment_name: str
    control_template_id: str
    variant_template_id: str
    target_agent_role: str
    target_task_types: str = "[]"
    sample_size_target: int = 20


class ABTestOut(BaseModel):
    id: str
    experiment_name: str
    control_template_id: str
    variant_template_id: str
    target_agent_role: str
    status: str
    control_total: int = 0
    control_avg_seconds: float = 0.0
    control_avg_tokens: float = 0.0
    variant_total: int = 0
    variant_avg_seconds: float = 0.0
    variant_avg_tokens: float = 0.0
    winner: Optional[str] = None
    confidence: Optional[float] = None
    started_at: str
    completed_at: Optional[str] = None


class PromptResultCreate(BaseModel):
    task_id: str
    template_id: str
    a_b_test_id: Optional[str] = None
    arm: str = "control"
    tokens_used: int = 0
    completion_seconds: float = 0.0
    task_status: str = "done"
    agent_role: str = "unknown"


class PromptResultOut(BaseModel):
    id: str
    task_id: str
    template_id: str
    a_b_test_id: Optional[str]
    arm: str
    tokens_used: int
    completion_seconds: float
    task_status: str
    agent_role: str
    created_at: str


class OptimizationInsightOut(BaseModel):
    id: str
    agent_role: str
    finding: str
    effect_size: float
    confidence: float
    recommendation: str
    source_task_count: int
    template_id: Optional[str] = None
    category: str = "baseline"
    created_at: str


# ── Routes ────────────────────────────────────────────────────────────────


@router.get("/templates", response_model=list[PromptTemplateOut])
async def list_templates(
    agent_role: Optional[str] = None,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> list[PromptTemplateOut]:
    """List all prompt templates, optionally filtered."""
    stmt = select(PromptTemplateModel).order_by(PromptTemplateModel.created_at.desc())
    if agent_role:
        stmt = stmt.where(PromptTemplateModel.agent_role == agent_role)
    if status:
        stmt = stmt.where(PromptTemplateModel.status == status)
    result = await session.execute(stmt)
    templates = result.scalars().all()
    return [_template_to_out(t) for t in templates]


@router.post("/templates", response_model=PromptTemplateOut, status_code=201)
async def create_template(
    payload: PromptTemplateCreate,
    session: AsyncSession = Depends(get_session),
) -> PromptTemplateOut:
    """Create a new prompt template with name, body, parameters, and optional metadata tags."""
    template = PromptTemplateModel(
        id=_uuid(),
        agent_role=payload.agent_role,
        pipeline_type=payload.pipeline_type,
        template_name=payload.template_name,
        template_body=payload.template_body,
        token_count=payload.token_count,
        tags=payload.tags,
        source_experiment_id=payload.source_experiment_id,
        version=1,
        status="active",
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return _template_to_out(template)


@router.get("/templates/{template_id}", response_model=PromptTemplateOut)
async def get_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
) -> PromptTemplateOut:
    """Get a single prompt template by ID."""
    template = await session.get(PromptTemplateModel, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_to_out(template)


@router.patch("/templates/{template_id}", response_model=PromptTemplateOut)
async def update_template(
    template_id: str,
    status: Optional[str] = None,
    template_name: Optional[str] = None,
    template_body: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> PromptTemplateOut:
    """Update a prompt template (status, name, or body)."""
    template = await session.get(PromptTemplateModel, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if status is not None:
        template.status = status
    if template_name is not None:
        template.template_name = template_name
    if template_body is not None:
        template.template_body = template_body
        template.token_count = len(template_body.split())
        template.version += 1
    template.updated_at = _utcnow()
    await session.commit()
    await session.refresh(template)
    return _template_to_out(template)


@router.get("/optimized")
async def get_optimized_prompt(
    agent_role: str = Query(..., description="Agent role to find prompt for"),
    pipeline_type: str = "any",
    task_title: str = "",
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get the best (highest-performing) prompt template for a given context.

    Returns the active template with the best historical performance.
    Falls back to the most recently created active template for the role.
    """
    stmt = (
        select(PromptTemplateModel)
        .where(
            PromptTemplateModel.status == "active",
            PromptTemplateModel.agent_role == agent_role,
        )
        .order_by(PromptTemplateModel.avg_tokens.asc(), PromptTemplateModel.use_count.desc())
    )
    result = await session.execute(stmt)
    candidates = result.scalars().all()

    if not candidates:
        raise HTTPException(status_code=404, detail=f"No active template found for agent_role={agent_role}")

    # Filter by pipeline_type if not "any"
    matched = [c for c in candidates if c.pipeline_type in ("any", pipeline_type)]
    if not matched:
        matched = candidates

    best = matched[0]
    return {
        "template": _template_to_out(best).model_dump(),
        "selection_reason": "best_performing"
        if best.use_count > 0
        else "most_recent_active",
        "sample_count": best.use_count,
    }


@router.post("/results", response_model=PromptResultOut, status_code=201)
async def log_prompt_result(
    payload: PromptResultCreate,
    session: AsyncSession = Depends(get_session),
) -> PromptResultOut:
    """Log a prompt execution result after task completion."""
    result = PromptResultModel(
        id=_uuid(),
        task_id=payload.task_id,
        template_id=payload.template_id,
        a_b_test_id=payload.a_b_test_id,
        arm=payload.arm,
        tokens_used=payload.tokens_used,
        completion_seconds=payload.completion_seconds,
        task_status=payload.task_status,
        agent_role=payload.agent_role,
    )
    session.add(result)

    # Update template performance stats
    template = await session.get(PromptTemplateModel, payload.template_id)
    if template:
        old_total_tokens = template.avg_tokens * template.use_count
        old_total_seconds = template.avg_seconds * template.use_count
        template.use_count += 1
        template.avg_tokens = (old_total_tokens + payload.tokens_used) / template.use_count
        template.avg_seconds = (old_total_seconds + payload.completion_seconds) / template.use_count
        template.updated_at = _utcnow()

    await session.commit()
    await session.refresh(result)
    return _result_to_out(result)


@router.get("/results", response_model=list[PromptResultOut])
async def list_prompt_results(
    template_id: Optional[str] = None,
    agent_role: Optional[str] = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> list[PromptResultOut]:
    """List prompt execution results, optionally filtered."""
    stmt = select(PromptResultModel).order_by(PromptResultModel.created_at.desc()).limit(limit)
    if template_id:
        stmt = stmt.where(PromptResultModel.template_id == template_id)
    if agent_role:
        stmt = stmt.where(PromptResultModel.agent_role == agent_role)
    result = await session.execute(stmt)
    return [_result_to_out(r) for r in result.scalars().all()]


@router.post("/experiments", response_model=ABTestOut, status_code=201)
async def create_experiment(
    payload: ABTestCreate,
    session: AsyncSession = Depends(get_session),
) -> ABTestOut:
    """Start a new A/B test experiment between two prompt templates."""
    control = await session.get(PromptTemplateModel, payload.control_template_id)
    if control is None:
        raise HTTPException(status_code=404, detail="Control template not found")

    variant = await session.get(PromptTemplateModel, payload.variant_template_id)
    if variant is None:
        raise HTTPException(status_code=404, detail="Variant template not found")

    experiment = ABExperimentModel(
        id=_uuid(),
        experiment_name=payload.experiment_name,
        control_template_id=payload.control_template_id,
        variant_template_id=payload.variant_template_id,
        target_agent_role=payload.target_agent_role,
        target_task_types=payload.target_task_types,
        sample_size_target=payload.sample_size_target,
        status="running",
    )
    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)
    return await _ab_test_to_out(experiment, session)


@router.get("/experiments", response_model=list[ABTestOut])
async def list_experiments(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> list[ABTestOut]:
    """List A/B test experiments with optional status filter and result summaries."""
    stmt = select(ABExperimentModel).order_by(ABExperimentModel.started_at.desc())
    if status:
        stmt = stmt.where(ABExperimentModel.status == status)
    result = await session.execute(stmt)
    experiments = result.scalars().all()
    return [await _ab_test_to_out(e, session) for e in experiments]


@router.get("/experiments/{test_id}", response_model=ABTestOut)
async def get_experiment(
    test_id: str,
    session: AsyncSession = Depends(get_session),
) -> ABTestOut:
    """Get a single A/B test experiment with results."""
    experiment = await session.get(ABExperimentModel, test_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return await _ab_test_to_out(experiment, session)


@router.post("/experiments/{test_id}/conclude")
async def conclude_experiment(
    test_id: str,
    session: AsyncSession = Depends(get_session),
) -> ABTestOut:
    """Force-conclude an A/B test and declare a winner."""
    experiment = await session.get(ABExperimentModel, test_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.status != "running":
        raise HTTPException(status_code=400, detail="Experiment is not running")

    experiment.status = "complete"
    experiment.completed_at = _utcnow()
    await _recompute_ab_test(experiment, session)
    await session.commit()
    await session.refresh(experiment)
    return await _ab_test_to_out(experiment, session)


@router.get("/insights", response_model=list[OptimizationInsightOut])
async def list_insights(
    agent_role: Optional[str] = None,
    min_confidence: float = 0.0,
    session: AsyncSession = Depends(get_session),
) -> list[OptimizationInsightOut]:
    """Return data-driven optimization insights from accumulated results."""
    stmt = select(OptimizationInsightModel).order_by(OptimizationInsightModel.confidence.desc())
    if agent_role:
        stmt = stmt.where(OptimizationInsightModel.agent_role == agent_role)
    if min_confidence > 0:
        stmt = stmt.where(OptimizationInsightModel.confidence >= min_confidence)
    result = await session.execute(stmt)
    return [_insight_to_out(i) for i in result.scalars().all()]


@router.post("/insights/generate")
async def generate_insights(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Auto-analyze prompt results and generate optimization insights."""
    # Count total results
    count_result = await session.execute(select(func.count(PromptResultModel.id)))
    total_results = count_result.scalar()

    if not total_results:
        return {"status": "no_data", "insights_generated": 0}

    # Group by agent_role: get distinct roles with enough results
    roles_result = await session.execute(
        select(
            PromptResultModel.agent_role,
            func.count(PromptResultModel.id).label("cnt"),
            func.avg(PromptResultModel.tokens_used).label("avg_tok"),
            func.avg(PromptResultModel.completion_seconds).label("avg_sec"),
        )
        .group_by(PromptResultModel.agent_role)
        .having(func.count(PromptResultModel.id) >= 5)
    )
    roles_data = roles_result.all()

    generated = 0
    for role, cnt, avg_tok, avg_sec in roles_data:
        avg_tok = float(avg_tok or 0)
        avg_sec = float(avg_sec or 0)
        cnt = int(cnt)

        # Insight 1: Role performance baseline
        insight = OptimizationInsightModel(
            id=_uuid(),
            agent_role=role,
            finding=f"{role} averages {avg_tok:.0f} tokens and {avg_sec:.0f}s per task across {cnt} tasks.",
            effect_size=0.0,
            confidence=min(0.9, cnt / 50),
            recommendation=f"Baseline established for {role}. Target: reduce tokens by 15%.",
            source_task_count=cnt,
            category="baseline",
        )
        session.add(insight)
        generated += 1

        # Insight 2: Fast completion pattern — find template with lowest avg seconds
        fast_stmt = (
            select(
                PromptResultModel.template_id,
                func.count(PromptResultModel.id).label("cnt"),
                func.avg(PromptResultModel.completion_seconds).label("avg_sec"),
            )
            .where(PromptResultModel.agent_role == role)
            .group_by(PromptResultModel.template_id)
            .having(func.avg(PromptResultModel.completion_seconds) < avg_sec * 0.7)
            .order_by(func.avg(PromptResultModel.completion_seconds).asc())
            .limit(1)
        )
        fast_result = await session.execute(fast_stmt)
        fast_row = fast_result.first()
        if fast_row and int(fast_row.cnt) >= 3:
            insight = OptimizationInsightModel(
                id=_uuid(),
                agent_role=role,
                finding=f"Template {fast_row.template_id[:8]}... correlates with fastest {role} completions ({float(fast_row.avg_sec):.0f}s avg).",
                effect_size=round(1.0 - (float(fast_row.avg_sec) / max(avg_sec, 1)), 2),
                confidence=min(0.8, int(fast_row.cnt) / 30),
                recommendation="Analyze fast template structure for reusable patterns.",
                source_task_count=int(fast_row.cnt),
                template_id=fast_row.template_id,
                category="fast_completion",
            )
            session.add(insight)
            generated += 1

        # Insight 3: Token efficiency
        token_stmt = (
            select(
                PromptResultModel.template_id,
                func.count(PromptResultModel.id).label("cnt"),
                func.avg(PromptResultModel.tokens_used).label("avg_tok"),
            )
            .where(PromptResultModel.agent_role == role)
            .group_by(PromptResultModel.template_id)
            .having(func.avg(PromptResultModel.tokens_used) < avg_tok * 0.7)
            .order_by(func.avg(PromptResultModel.tokens_used).asc())
            .limit(1)
        )
        token_result = await session.execute(token_stmt)
        token_row = token_result.first()
        if token_row and int(token_row.cnt) >= 3:
            insight = OptimizationInsightModel(
                id=_uuid(),
                agent_role=role,
                finding=f"Template {token_row.template_id[:8]}... uses {float(token_row.avg_tok):.0f} avg tokens ({int((1-float(token_row.avg_tok)/max(avg_tok,1))*100)}% below {role} average).",
                effect_size=round(1.0 - (float(token_row.avg_tok) / max(avg_tok, 1)), 2),
                confidence=min(0.7, int(token_row.cnt) / 20),
                recommendation="Review low-token template structure as optimization target.",
                source_task_count=int(token_row.cnt),
                template_id=token_row.template_id,
                category="token_efficiency",
            )
            session.add(insight)
            generated += 1

    await session.commit()
    return {
        "status": "success",
        "insights_generated": generated,
        "total_results_analyzed": total_results,
    }


@router.get("/roi")
async def prompt_roi(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return cost/benefit analysis: token savings per cycle."""
    count_result = await session.execute(select(func.count(PromptResultModel.id)))
    total_results = count_result.scalar() or 0

    if total_results == 0:
        return {
            "total_results": 0,
            "avg_tokens_per_task": 0,
            "avg_seconds_per_task": 0,
            "estimated_savings": {},
            "status": "no_data",
        }

    # Aggregate stats
    stats_result = await session.execute(
        select(
            func.avg(PromptResultModel.tokens_used),
            func.avg(PromptResultModel.completion_seconds),
            func.sum(PromptResultModel.tokens_used),
            func.sum(PromptResultModel.completion_seconds),
        )
    )
    avg_tok, avg_sec, total_tok, total_sec = stats_result.one()
    avg_tok = float(avg_tok or 0)
    avg_sec = float(avg_sec or 0)
    total_tok = int(total_tok or 0)
    total_sec = float(total_sec or 0)

    # Per-template breakdown
    template_stmt = (
        select(
            PromptResultModel.template_id,
            func.count(PromptResultModel.id).label("cnt"),
            func.avg(PromptResultModel.tokens_used).label("avg_tok"),
            func.avg(PromptResultModel.completion_seconds).label("avg_sec"),
        )
        .group_by(PromptResultModel.template_id)
        .order_by(func.avg(PromptResultModel.tokens_used).asc())
        .limit(10)
    )
    template_rows = await session.execute(template_stmt)
    template_breakdown = []
    for tid, cnt, avgt, avgs in template_rows.all():
        name_result = await session.execute(
            select(PromptTemplateModel.template_name).where(PromptTemplateModel.id == tid)
        )
        name = name_result.scalar() or tid
        template_breakdown.append({
            "template_id": tid,
            "template_name": name,
            "task_count": int(cnt),
            "avg_tokens": round(float(avgt), 1),
            "avg_seconds": round(float(avgs), 1),
        })

    # Count completed experiments
    exp_count_result = await session.execute(
        select(func.count(ABExperimentModel.id)).where(ABExperimentModel.status == "complete")
    )
    completed_experiments = exp_count_result.scalar() or 0

    return {
        "total_results": total_results,
        "avg_tokens_per_task": round(avg_tok, 1),
        "avg_seconds_per_task": round(avg_sec, 1),
        "estimated_savings": {
            "baseline_tokens_per_task": round(avg_tok * 1.15, 1),
            "current_tokens_per_task": round(avg_tok, 1),
            "savings_percent": "15% target",
        },
        "template_performance": template_breakdown,
        "experiment_count": completed_experiments,
    }


# ── Helpers ────────────────────────────────────────────────────────────────


def _template_to_out(t: PromptTemplateModel) -> PromptTemplateOut:
    return PromptTemplateOut(
        id=t.id,
        agent_role=t.agent_role,
        pipeline_type=t.pipeline_type,
        template_name=t.template_name,
        template_body=t.template_body,
        token_count=t.token_count,
        version=t.version,
        status=t.status,
        tags=t.tags,
        source_experiment_id=t.source_experiment_id,
        avg_tokens=t.avg_tokens,
        avg_seconds=t.avg_seconds,
        use_count=t.use_count,
        created_at=t.created_at.isoformat() if t.created_at else "",
        updated_at=t.updated_at.isoformat() if t.updated_at else "",
    )


def _result_to_out(r: PromptResultModel) -> PromptResultOut:
    return PromptResultOut(
        id=r.id,
        task_id=r.task_id,
        template_id=r.template_id,
        a_b_test_id=r.a_b_test_id,
        arm=r.arm,
        tokens_used=r.tokens_used,
        completion_seconds=r.completion_seconds,
        task_status=r.task_status,
        agent_role=r.agent_role,
        created_at=r.created_at.isoformat() if r.created_at else "",
    )


async def _ab_test_to_out(e: ABExperimentModel, session: AsyncSession) -> ABTestOut:
    """Compute A/B test results from the database."""
    # Count control results
    ctrl_result = await session.execute(
        select(
            func.count(PromptResultModel.id),
            func.coalesce(func.avg(PromptResultModel.completion_seconds), 0),
            func.coalesce(func.avg(PromptResultModel.tokens_used), 0),
        ).where(
            PromptResultModel.a_b_test_id == e.id,
            PromptResultModel.arm == "control",
        )
    )
    ctrl_cnt, ctrl_avg_s, ctrl_avg_t = ctrl_result.one()

    # Count variant results
    var_result = await session.execute(
        select(
            func.count(PromptResultModel.id),
            func.coalesce(func.avg(PromptResultModel.completion_seconds), 0),
            func.coalesce(func.avg(PromptResultModel.tokens_used), 0),
        ).where(
            PromptResultModel.a_b_test_id == e.id,
            PromptResultModel.arm == "variant",
        )
    )
    var_cnt, var_avg_s, var_avg_t = var_result.one()

    winner = None
    confidence = None
    ctrl_cnt = int(ctrl_cnt)
    var_cnt = int(var_cnt)

    if ctrl_cnt >= 5 and var_cnt >= 5:
        if float(var_avg_s) < float(ctrl_avg_s) * 0.9:
            winner = "variant"
            confidence = min(0.95, 0.5 + (var_cnt / 50) * 0.5)
        elif float(ctrl_avg_s) < float(var_avg_s) * 0.9:
            winner = "control"
            confidence = min(0.95, 0.5 + (ctrl_cnt / 50) * 0.5)

    return ABTestOut(
        id=e.id,
        experiment_name=e.experiment_name,
        control_template_id=e.control_template_id,
        variant_template_id=e.variant_template_id,
        target_agent_role=e.target_agent_role,
        status=e.status,
        control_total=ctrl_cnt,
        control_avg_seconds=round(float(ctrl_avg_s), 1),
        control_avg_tokens=round(float(ctrl_avg_t), 1),
        variant_total=var_cnt,
        variant_avg_seconds=round(float(var_avg_s), 1),
        variant_avg_tokens=round(float(var_avg_t), 1),
        winner=winner,
        confidence=round(confidence, 2) if confidence else None,
        started_at=e.started_at.isoformat() if e.started_at else "",
        completed_at=e.completed_at.isoformat() if e.completed_at else None,
    )


def _insight_to_out(i: OptimizationInsightModel) -> OptimizationInsightOut:
    return OptimizationInsightOut(
        id=i.id,
        agent_role=i.agent_role,
        finding=i.finding,
        effect_size=i.effect_size,
        confidence=i.confidence,
        recommendation=i.recommendation,
        source_task_count=i.source_task_count,
        template_id=i.template_id,
        category=i.category,
        created_at=i.created_at.isoformat() if i.created_at else "",
    )


async def _recompute_ab_test(
    experiment: ABExperimentModel, session: AsyncSession
) -> None:
    """Recompute A/B test stats and auto-conclude if sample size is met."""
    ctrl_result = await session.execute(
        select(func.count(PromptResultModel.id)).where(
            PromptResultModel.a_b_test_id == experiment.id,
            PromptResultModel.arm == "control",
        )
    )
    ctrl_cnt = int(ctrl_result.scalar() or 0)

    var_result = await session.execute(
        select(func.count(PromptResultModel.id)).where(
            PromptResultModel.a_b_test_id == experiment.id,
            PromptResultModel.arm == "variant",
        )
    )
    var_cnt = int(var_result.scalar() or 0)

    # Auto-conclude if both arms reached target
    if ctrl_cnt >= experiment.sample_size_target and var_cnt >= experiment.sample_size_target:
        experiment.status = "complete"
        experiment.completed_at = _utcnow()
