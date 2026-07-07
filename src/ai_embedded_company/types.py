"""Shared type definitions for AI Embedded Company.

These types are used across the API, MCP tools, orchestrator, and storage layers.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PipelinePhase(str, enum.Enum):
    IDEA = "idea"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOY = "deploy"
    DONE = "done"


class PipelineType(str, enum.Enum):
    EMBEDDED_FIRMWARE = "embedded-firmware"
    EMBEDDED_LINUX = "embedded-linux"
    WEB_FULLSTACK = "web-fullstack"
    QUICK_PROTOTYPE = "quick-prototype"
    RESEARCH_SPIKE = "research-spike"


class AgentRole(str, enum.Enum):
    FIRMWARE_ENGINEER = "embedded-firmware-engineer"
    HARDWARE_ENGINEER = "embedded-hardware-engineer"
    LINUX_ENGINEER = "embedded-linux-engineer"
    IOT_ENGINEER = "embedded-iot-engineer"
    SENSOR_DRIVER_DEV = "embedded-sensor-driver-dev"
    TESTING_ENGINEER = "embedded-testing-engineer"
    SOFTWARE_ARCHITECT = "software-architect"
    BACKEND_DEVELOPER = "backend-developer"
    FRONTEND_DEVELOPER = "frontend-developer"
    FULLSTACK_DEVELOPER = "fullstack-developer"
    DEVOPS_ENGINEER = "devops-engineer"
    SECURITY_ENGINEER = "security-engineer"
    TECH_LEAD = "tech-lead"
    PROJECT_MANAGER = "project-manager"
    CODE_REVIEWER = "code-reviewer"
    QA_ENGINEER = "qa-engineer"
    TECHNICAL_WRITER = "technical-writer"
    IDEA_REFINER = "idea-refiner"
    RAPID_PROTOTYPER = "rapid-prototyper"


class BoardFamily(str, enum.Enum):
    ESP32 = "esp32"
    ESP32_S3 = "esp32-s3"
    STM32 = "stm32"
    RP2040 = "rp2040"
    NRF52 = "nrf52"
    UNKNOWN = "unknown"


# ── Pydantic Models — Project ────────────────────────────────────────────────


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=1024)
    board_family: BoardFamily = Field(default=BoardFamily.UNKNOWN)
    board_model: str = Field(default="", max_length=64)


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str = Field(..., description="UUID string")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# ── Pydantic Models — Task ───────────────────────────────────────────────────


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=4096)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    assigned_agent: Optional[AgentRole] = None


class TaskCreate(TaskBase):
    project_id: str
    parent_task_id: Optional[str] = None
    estimated_minutes: Optional[int] = None


class Task(TaskBase):
    id: str = Field(..., description="UUID string")
    project_id: str
    parent_task_id: Optional[str] = None
    status: TaskStatus = Field(default=TaskStatus.TODO)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_seconds: int = 0
    last_paused_at: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# ── Pydantic Models — Idea ───────────────────────────────────────────────────


class IdeaBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    raw_description: str = Field(default="", max_length=8192)
    tags: list[str] = Field(default_factory=list)


class IdeaCreate(IdeaBase):
    pass


class Idea(IdeaBase):
    id: str = Field(..., description="UUID string")
    refined_description: Optional[str] = None
    suggested_pipeline: Optional[PipelineType] = None
    status: str = "new"  # new, refining, approved, rejected, in_progress, done
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# ── Pydantic Models — Pipeline ───────────────────────────────────────────────


class PipelineStep(BaseModel):
    phase: PipelinePhase
    name: str
    description: str = ""
    assigned_agent: Optional[AgentRole] = None
    status: TaskStatus = TaskStatus.TODO


class PipelineCreate(BaseModel):
    project_id: str
    pipeline_type: PipelineType
    idea_id: Optional[str] = None


class Pipeline(PipelineCreate):
    id: str = Field(..., description="UUID string")
    steps: list[PipelineStep] = Field(default_factory=list)
    current_phase: PipelinePhase = Field(default=PipelinePhase.IDEA)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


# ── Pydantic Models — Team & Agent ───────────────────────────────────────────


class AgentInfo(BaseModel):
    name: str
    role: AgentRole
    status: str = "idle"  # idle, busy, offline
    current_task_id: Optional[str] = None
    expertise: list[str] = Field(default_factory=list)


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    project_id: str
    members: list[AgentRole] = Field(default_factory=list)


class Team(TeamCreate):
    id: str = Field(..., description="UUID string")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Pydantic Models — Knowledge ──────────────────────────────────────────────


class KnowledgeEntry(BaseModel):
    id: str = Field(..., description="UUID string")
    title: str
    content: str
    category: str  # pinout, datasheet, code-pattern, bug-fix, tip
    tags: list[str] = Field(default_factory=list)
    board_family: Optional[BoardFamily] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Pydantic Models — Hardware ───────────────────────────────────────────────


class BoardInfo(BaseModel):
    model: str
    family: BoardFamily
    chip: str
    manufacturer: str
    pinout_url: Optional[str] = None
    specs: dict[str, Any] = Field(default_factory=dict)


class SerialPortInfo(BaseModel):
    device: str
    description: str = ""
    vid: Optional[str] = None
    pid: Optional[str] = None
    serial_number: Optional[str] = None


class BuildResult(BaseModel):
    success: bool
    output: str
    binary_path: Optional[str] = None
    flash_size: Optional[int] = None
    ram_usage: Optional[int] = None
