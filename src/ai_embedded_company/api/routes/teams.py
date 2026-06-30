"""Team management API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import TeamModel
from ai_embedded_company.types import Team, TeamCreate

router = APIRouter()


@router.post("/", response_model=Team, status_code=201)
async def create_team(
    payload: TeamCreate,
    session: AsyncSession = Depends(get_session),
) -> Team:
    """Create a new agent team."""
    team = TeamModel(
        name=payload.name,
        project_id=payload.project_id,
        members=json.dumps([m.value if hasattr(m, 'value') else m for m in payload.members]),
    )
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return _model_to_team(team)


@router.get("/", response_model=list[Team])
async def list_teams(
    project_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Team]:
    """List teams, optionally filtered by project."""
    stmt = select(TeamModel)
    if project_id:
        stmt = stmt.where(TeamModel.project_id == project_id)
    result = await session.execute(stmt)
    return [_model_to_team(m) for m in result.scalars().all()]


@router.get("/{team_id}", response_model=Team)
async def get_team(
    team_id: str,
    session: AsyncSession = Depends(get_session),
) -> Team:
    """Get a single team by ID."""
    result = await session.execute(
        select(TeamModel).where(TeamModel.id == team_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return _model_to_team(model)


def _model_to_team(m: TeamModel) -> Team:
    try:
        members = json.loads(m.members) if m.members else []
    except json.JSONDecodeError:
        members = []
    return Team(
        id=m.id,
        name=m.name,
        project_id=m.project_id,
        members=members,
        created_at=m.created_at,
    )
