"""Project CRUD routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import ProjectModel
from ai_embedded_company.types import Project, ProjectCreate, ProjectStatus

router = APIRouter()


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
