"""Self-evolution API routes — failure alchemy, research loop, knowledge health."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import FailureRecord, ResearchFinding

router = APIRouter()


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


@router.get("/research")
async def list_research(
    status: str | None = None,
    source_type: str | None = None,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """List research findings."""
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
