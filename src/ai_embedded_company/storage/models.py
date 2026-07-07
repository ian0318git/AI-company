"""SQLAlchemy ORM models for AI Embedded Company."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Type alias for Optional datetime to keep annotations clean
_opt_dt = datetime | None

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

    # ── Time Tracking ─────────────────────────────────────
    started_at: Mapped[_opt_dt] = mapped_column(DateTime, nullable=True, default=None)
    """When the task first transitioned to in_progress."""
    completed_at: Mapped[_opt_dt] = mapped_column(DateTime, nullable=True, default=None)
    """When the task transitioned to done."""
    paused_seconds: Mapped[int] = mapped_column(Integer, default=0)
    """Total seconds the task spent in a paused state (blocked/review) while timer was running."""
    last_paused_at: Mapped[_opt_dt] = mapped_column(DateTime, nullable=True, default=None)
    """When the current pause period started, if the timer is currently paused."""
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    """Optional estimated effort in minutes."""

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


# ── Self-Evolution: Failure Alchemy ───────────────────────────────────────────


class FailureRecord(Base):
    """Antibody: failure experience stored to prevent future recurrence."""
    __tablename__ = "failure_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
    agent_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    root_cause: Mapped[str] = mapped_column(Text, default="")  # Extracted root cause
    category: Mapped[str] = mapped_column(String(64), default="unknown")
    # categories: logic_error, resource_leak, race_condition, config_miss, dependency, timeout, api_error, security
    severity: Mapped[str] = mapped_column(String(32), default="medium")  # low, medium, high, critical
    frequency: Mapped[int] = mapped_column(Integer, default=1)  # How many times this pattern occurred
    antibody: Mapped[str] = mapped_column(Text, default="")  # Prevention strategy
    vaccine: Mapped[str] = mapped_column(Text, default="")  # Pre-task warning to inject
    catalyst: Mapped[str] = mapped_column(Text, default="")  # Prompt improvement to inject
    status: Mapped[str] = mapped_column(String(32), default="analyzed")  # reported, analyzed, resolved, archived
    tags: Mapped[str] = mapped_column(String(1024), default="")  # JSON-encoded list
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ── Self-Evolution: Research Findings ─────────────────────────────────────────


class ResearchFinding(Base):
    """Findings from the research agent loop — feeds into brainstorming."""
    __tablename__ = "research_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    source: Mapped[str] = mapped_column(String(256), default="")  # URL, paper, tool name
    source_type: Mapped[str] = mapped_column(String(64), default="web")
    # source_type: competitor, framework, paper, tool, pattern, trend
    summary: Mapped[str] = mapped_column(Text, default="")
    relevance_score: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    debate_notes: Mapped[str] = mapped_column(Text, default="")  # Agent debate output
    action_items: Mapped[str] = mapped_column(Text, default="")  # JSON list of follow-up tasks
    idea_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("ideas.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new")
    # new, debated, accepted, rejected, implemented
    tags: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
