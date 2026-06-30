"""SQLAlchemy ORM models for AI Embedded Company."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_embedded_company.storage.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Project ──────────────────────────────────────────────────────────────────


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    board_family: Mapped[str] = mapped_column(String(32), default="unknown")
    board_model: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    tasks: Mapped[list["TaskModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    ideas: Mapped[list["IdeaModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


# ── Task ─────────────────────────────────────────────────────────────────────


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    parent_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(4096), default="")
    status: Mapped[str] = mapped_column(String(32), default="todo")
    priority: Mapped[str] = mapped_column(String(32), default="medium")
    assigned_agent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    project: Mapped["ProjectModel"] = relationship(back_populates="tasks")
    subtasks: Mapped[list["TaskModel"]] = relationship(
        back_populates="parent", remote_side="TaskModel.id"
    )
    parent: Mapped["TaskModel | None"] = relationship(
        back_populates="subtasks", remote_side="TaskModel.parent_task_id"
    )


# ── Idea ─────────────────────────────────────────────────────────────────────


class IdeaModel(Base):
    __tablename__ = "ideas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    raw_description: Mapped[str] = mapped_column(String(8192), default="")
    refined_description: Mapped[str | None] = mapped_column(String(8192), nullable=True)
    tags: Mapped[str] = mapped_column(String(1024), default="")  # JSON-encoded list
    suggested_pipeline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    project: Mapped["ProjectModel | None"] = relationship(back_populates="ideas")


# ── Pipeline ─────────────────────────────────────────────────────────────────


class PipelineModel(Base):
    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    pipeline_type: Mapped[str] = mapped_column(String(64), nullable=False)
    idea_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ideas.id"), nullable=True)
    steps: Mapped[str] = mapped_column(Text, default="[]")  # JSON-encoded list[PipelineStep]
    current_phase: Mapped[str] = mapped_column(String(32), default="idea")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ── Team ─────────────────────────────────────────────────────────────────────


class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    members: Mapped[str] = mapped_column(Text, default="[]")  # JSON-encoded list[AgentRole]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ── Knowledge ────────────────────────────────────────────────────────────────


class KnowledgeModel(Base):
    __tablename__ = "knowledge"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(32), default="tip")
    tags: Mapped[str] = mapped_column(String(1024), default="")  # JSON-encoded list
    board_family: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ── Event Log ────────────────────────────────────────────────────────────────


class EventLogModel(Base):
    __tablename__ = "event_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(128), default="")
    payload: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
