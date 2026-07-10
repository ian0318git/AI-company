"""Idea capture, retrieval, refinement, and workflow bootstrap routes."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.api.pagination import paginate_query
from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import (
    IdeaModel,
    PipelineModel,
    ProjectModel,
    TaskModel,
    TeamModel,
)
from ai_embedded_company.types import AgentRole, Idea, IdeaCreate, PaginatedResponse

router = APIRouter()

# ── Pipeline step and agent definitions per type ──────────────────────────────

_PIPELINE_DEFS: dict[str, dict] = {
    "research-spike": {
        "phases": [
            {"phase": "idea", "name": "Define research scope", "agent": AgentRole.IDEA_REFINER},
            {"phase": "requirements", "name": "Identify sources & methodology", "agent": AgentRole.TECH_LEAD},
            {"phase": "design", "name": "Structure report outline", "agent": AgentRole.TECHNICAL_WRITER},
            {"phase": "implementation", "name": "Gather data & write analysis", "agent": AgentRole.TECHNICAL_WRITER},
            {"phase": "testing", "name": "Verify sources & fact-check", "agent": AgentRole.QA_ENGINEER},
            {"phase": "deploy", "name": "Finalize report & presentation", "agent": AgentRole.TECHNICAL_WRITER},
        ],
        "team": [AgentRole.IDEA_REFINER, AgentRole.TECH_LEAD, AgentRole.TECHNICAL_WRITER,
                 AgentRole.QA_ENGINEER, AgentRole.PROJECT_MANAGER],
        "seed_tasks": [
            "Define research questions and scope boundaries",
            "Identify academic databases and data sources",
            "Draft report outline and structure",
            "Gather employment statistics and trends",
            "Analyze AI impact on embedded/firmware roles",
            "Write analysis with citations",
            "Fact-check all claims and data points",
            "Create executive summary presentation",
        ],
    },
    "embedded-firmware": {
        "phases": [
            {"phase": "idea", "name": "Pin planning & feasibility", "agent": AgentRole.HARDWARE_ENGINEER},
            {"phase": "requirements", "name": "Define HAL interfaces", "agent": AgentRole.FIRMWARE_ENGINEER},
            {"phase": "design", "name": "Firmware architecture", "agent": AgentRole.FIRMWARE_ENGINEER},
            {"phase": "implementation", "name": "Write business logic & drivers", "agent": AgentRole.FIRMWARE_ENGINEER},
            {"phase": "testing", "name": "Unit tests & HIL validation", "agent": AgentRole.TESTING_ENGINEER},
            {"phase": "deploy", "name": "Flash to device & verify", "agent": AgentRole.FIRMWARE_ENGINEER},
        ],
        "team": [AgentRole.FIRMWARE_ENGINEER, AgentRole.HARDWARE_ENGINEER,
                 AgentRole.TESTING_ENGINEER, AgentRole.TECH_LEAD, AgentRole.PROJECT_MANAGER],
        "seed_tasks": [
            "Plan GPIO pin assignments and board connections",
            "Implement HAL layer for peripherals",
            "Write core business logic",
            "Implement error handling and watchdog",
            "Write unit tests for all modules",
            "Run HIL tests on target hardware",
            "Optimize memory and power usage",
            "Flash firmware and validate on device",
        ],
    },
    "embedded-linux": {
        "phases": [
            {"phase": "idea", "name": "System architecture design", "agent": AgentRole.SOFTWARE_ARCHITECT},
            {"phase": "requirements", "name": "Kernel config & BSP", "agent": AgentRole.LINUX_ENGINEER},
            {"phase": "design", "name": "Driver architecture", "agent": AgentRole.LINUX_ENGINEER},
            {"phase": "implementation", "name": "Driver & application development", "agent": AgentRole.LINUX_ENGINEER},
            {"phase": "testing", "name": "Cross-compile & integration test", "agent": AgentRole.TESTING_ENGINEER},
            {"phase": "deploy", "name": "Package & release image", "agent": AgentRole.DEVOPS_ENGINEER},
        ],
        "team": [AgentRole.LINUX_ENGINEER, AgentRole.SOFTWARE_ARCHITECT,
                 AgentRole.TESTING_ENGINEER, AgentRole.DEVOPS_ENGINEER, AgentRole.PROJECT_MANAGER],
        "seed_tasks": [
            "Define kernel configuration and device tree",
            "Write kernel driver for target hardware",
            "Implement user-space application",
            "Set up cross-compilation toolchain",
            "Run integration tests on target",
            "Create buildroot/yocto image recipe",
        ],
    },
    "web-fullstack": {
        "phases": [
            {"phase": "idea", "name": "UI/UX wireframes", "agent": AgentRole.FRONTEND_DEVELOPER},
            {"phase": "requirements", "name": "API design & data model", "agent": AgentRole.BACKEND_DEVELOPER},
            {"phase": "design", "name": "System architecture", "agent": AgentRole.SOFTWARE_ARCHITECT},
            {"phase": "implementation", "name": "Backend & frontend development", "agent": AgentRole.FULLSTACK_DEVELOPER},
            {"phase": "testing", "name": "Integration & E2E tests", "agent": AgentRole.QA_ENGINEER},
            {"phase": "deploy", "name": "Deploy to production", "agent": AgentRole.DEVOPS_ENGINEER},
        ],
        "team": [AgentRole.FRONTEND_DEVELOPER, AgentRole.BACKEND_DEVELOPER, AgentRole.FULLSTACK_DEVELOPER,
                 AgentRole.SOFTWARE_ARCHITECT, AgentRole.QA_ENGINEER, AgentRole.DEVOPS_ENGINEER,
                 AgentRole.PROJECT_MANAGER],
        "seed_tasks": [
            "Design database schema and API contracts",
            "Implement REST API endpoints",
            "Build frontend components and pages",
            "Connect frontend to backend API",
            "Write integration and E2E tests",
            "Set up CI/CD pipeline",
            "Deploy to staging and verify",
        ],
    },
    "quick-prototype": {
        "phases": [
            {"phase": "idea", "name": "Scope MVP", "agent": AgentRole.RAPID_PROTOTYPER},
            {"phase": "implementation", "name": "Build MVP", "agent": AgentRole.RAPID_PROTOTYPER},
            {"phase": "testing", "name": "Smoke test", "agent": AgentRole.QA_ENGINEER},
            {"phase": "deploy", "name": "Share prototype", "agent": AgentRole.RAPID_PROTOTYPER},
        ],
        "team": [AgentRole.RAPID_PROTOTYPER, AgentRole.QA_ENGINEER, AgentRole.PROJECT_MANAGER],
        "seed_tasks": [
            "Scope the minimum viable features",
            "Build core functionality",
            "Smoke test and fix critical bugs",
            "Prepare demo and share with stakeholders",
        ],
    },
}


# ── Agent Skill Registry ───────────────────────────────────────────────────────

_AGENT_SKILLS: dict[str, dict] = {
    "embedded-firmware-engineer": {
        "skills": ["c/c++", "rtos", "freertos", "hal", "driver", "firmware", "mcu",
                   "esp32", "stm32", "arm", "debugging", "jtag", "uart", "spi", "i2c",
                   "gpio", "pwm", "adc", "dma", "interrupt", "bootloader"],
        "keywords": ["韌體", "firmware", "mcu", "單晶片", "rtos", "driver", "驅動"],
    },
    "embedded-hardware-engineer": {
        "skills": ["pcb", "schematic", "power", "emi", "signal-integrity", "layout",
                   "oscilloscope", "multimeter", "gpio", "sensor", "actuator", "relay"],
        "keywords": ["硬體", "電路", "pcb", "layout", "power", "電源", "腳位", "pin"],
    },
    "embedded-linux-engineer": {
        "skills": ["linux", "kernel", "buildroot", "yocto", "device-tree", "cross-compile",
                   "driver", "embedded-linux", "systemd", "networking"],
        "keywords": ["linux", "kernel", "buildroot", "yocto", "樹莓派", "raspberry"],
    },
    "embedded-iot-engineer": {
        "skills": ["mqtt", "coap", "ble", "wifi", "lora", "zigbee", "ota", "cloud",
                   "aws-iot", "azure-iot", "tcp/ip", "tls", "低功耗", "mesh"],
        "keywords": ["wifi", "ble", "mqtt", "iot", "物聯網", "雲端", "cloud", "ota", "lora", "zigbee"],
    },
    "embedded-sensor-driver-dev": {
        "skills": ["i2c", "spi", "uart", "sensor", "imu", "temperature", "humidity",
                   "pressure", "accelerometer", "gyroscope", "magnetometer", "adc"],
        "keywords": ["sensor", "感測器", "i2c", "spi", "溫度", "濕度", "壓力", "加速度"],
    },
    "embedded-testing-engineer": {
        "skills": ["unit-test", "hil", "integration-test", "ci/cd", "coverage",
                   "static-analysis", "memory-analysis", "power-analysis"],
        "keywords": ["測試", "test", "驗證", "hil", "coverage"],
    },
    "software-architect": {
        "skills": ["architecture", "design-patterns", "system-design", "microservices",
                   "api-design", "database", "scalability", "technical-spec"],
        "keywords": ["架構", "architecture", "系統設計", "system design"],
    },
    "backend-developer": {
        "skills": ["python", "fastapi", "sql", "postgresql", "redis", "rest", "graphql",
                   "docker", "aws", "api", "database"],
        "keywords": ["後端", "api", "backend", "server", "database", "資料庫"],
    },
    "frontend-developer": {
        "skills": ["react", "typescript", "css", "tailwind", "ui/ux", "frontend",
                   "responsive", "accessibility"],
        "keywords": ["前端", "frontend", "ui", "dashboard", "網頁", "react", "vue"],
    },
    "fullstack-developer": {
        "skills": ["python", "javascript", "react", "fastapi", "sql", "docker",
                   "fullstack", "prototype", "mvp"],
        "keywords": ["全端", "fullstack", "full stack", "web", "prototype"],
    },
    "devops-engineer": {
        "skills": ["docker", "kubernetes", "ci/cd", "aws", "terraform", "ansible",
                   "monitoring", "logging", "github-actions"],
        "keywords": ["部署", "deploy", "ci/cd", "docker", "kubernetes", "devops"],
    },
    "security-engineer": {
        "skills": ["penetration-testing", "code-audit", "tls", "authentication",
                   "authorization", "owasp", "secure-boot", "encryption"],
        "keywords": ["安全", "security", "加密", "encryption", "稽核", "audit", "滲透"],
    },
    "tech-lead": {
        "skills": ["architecture", "code-review", "mentoring", "technical-strategy",
                   "risk-assessment", "technology-selection"],
        "keywords": ["技術", "tech", "review", "審查", "決策"],
    },
    "project-manager": {
        "skills": ["planning", "scheduling", "risk-management", "stakeholder",
                   "agile", "scrum", "roadmap"],
        "keywords": ["管理", "進度", "時程", "milestone", "交付"],
    },
    "qa-engineer": {
        "skills": ["testing", "e2e", "regression", "test-automation", "bug-tracking",
                   "quality", "acceptance"],
        "keywords": ["測試", "qa", "品質", "驗收", "bug"],
    },
    "technical-writer": {
        "skills": ["documentation", "technical-writing", "api-docs", "user-guide",
                   "tutorial", "markdown", "diagram"],
        "keywords": ["文件", "document", "報告", "report", "簡報", "presentation", "分析"],
    },
    "idea-refiner": {
        "skills": ["requirements", "brainstorming", "research", "analysis",
                   "market-research", "feasibility"],
        "keywords": ["想法", "idea", "分析", "analysis", "研究", "research", "市場"],
    },
    "rapid-prototyper": {
        "skills": ["prototype", "mvp", "fast-iteration", "demo", "poc",
                   "proof-of-concept"],
        "keywords": ["原型", "prototype", "mvp", "快速", "demo", "示範"],
    },
    "code-reviewer": {
        "skills": ["code-review", "static-analysis", "best-practices", "refactoring",
                   "security-review", "performance"],
        "keywords": ["審查", "review", "refactor", "code quality", "程式碼品質"],
    },
}

# Skill → agent lookup (inverted index)
_SKILL_TO_AGENTS: dict[str, list[str]] = {}
for _agent_id, _data in _AGENT_SKILLS.items():
    for _skill in _data["skills"]:
        _SKILL_TO_AGENTS.setdefault(_skill, []).append(_agent_id)

# ── Agent workflow definitions (detailed execution plan per pipeline) ──────────

_AGENT_WORKFLOWS: dict[str, list[dict]] = {
    "research-spike": [
        {
            "id": "r1", "agent": "idea-refiner", "title": "Scope definition", "phase": "idea",
            "description": "Analyzes the raw idea, identifies knowledge gaps, defines research questions and scope boundaries.",
            "inputs": ["Raw idea description", "User context"],
            "outputs": ["Research scope document", "Key questions list"],
            "depends_on": [], "parallel_group": None,
        },
        {
            "id": "r2", "agent": "tech-lead", "title": "Source identification", "phase": "requirements",
            "description": "Identifies academic databases, industry reports, market data sources. Defines search methodology and quality criteria.",
            "inputs": ["Research scope document"],
            "outputs": ["Source inventory", "Methodology plan"],
            "depends_on": ["r1"], "parallel_group": None,
        },
        {
            "id": "r3a", "agent": "technical-writer", "title": "Report structure design", "phase": "design",
            "description": "Designs the report outline, section hierarchy, and key arguments flow.",
            "inputs": ["Methodology plan"],
            "outputs": ["Report outline", "Section templates"],
            "depends_on": ["r2"], "parallel_group": "design",
        },
        {
            "id": "r3b", "agent": "project-manager", "title": "Timeline & milestones", "phase": "design",
            "description": "Sets deliverable timeline, checkpoints, and review gates.",
            "inputs": ["Research scope document"],
            "outputs": ["Project timeline", "Milestone tracker"],
            "depends_on": ["r1"], "parallel_group": "design",
        },
        {
            "id": "r4a", "agent": "technical-writer", "title": "Data gathering & drafting", "phase": "implementation",
            "description": "Searches academic databases, industry sources. Compiles statistics, trends, and expert opinions into draft sections.",
            "inputs": ["Source inventory", "Report outline"],
            "outputs": ["Draft report sections", "Data tables"],
            "depends_on": ["r3a"], "parallel_group": "write",
        },
        {
            "id": "r4b", "agent": "idea-refiner", "title": "Competitive context research", "phase": "implementation",
            "description": "Researches parallel industry movements, competitor analyses, and adjacent market data for richer context.",
            "inputs": ["Research scope document"],
            "outputs": ["Context briefing", "Competitive landscape notes"],
            "depends_on": ["r1"], "parallel_group": "write",
        },
        {
            "id": "r5a", "agent": "qa-engineer", "title": "Fact-checking & source verification", "phase": "testing",
            "description": "Verifies every claim against original sources. Checks data accuracy, citation completeness, and logical consistency.",
            "inputs": ["Draft report sections", "Source inventory"],
            "outputs": ["Verification report", "Correction annotations"],
            "depends_on": ["r4a", "r4b"], "parallel_group": "verify",
        },
        {
            "id": "r5b", "agent": "tech-lead", "title": "Technical accuracy review", "phase": "testing",
            "description": "Reviews all technical claims. Ensures embedded/firmware domain terminology and analysis are correct.",
            "inputs": ["Draft report sections"],
            "outputs": ["Technical review notes", "Accuracy sign-off"],
            "depends_on": ["r4a", "r4b"], "parallel_group": "verify",
        },
        {
            "id": "r5c", "agent": "project-manager", "title": "Stakeholder pre-read", "phase": "testing",
            "description": "Reviews draft for stakeholder readiness. Checks executive summary impact and recommendation clarity.",
            "inputs": ["Draft report sections"],
            "outputs": ["Stakeholder feedback", "Presentation readiness score"],
            "depends_on": ["r4a"], "parallel_group": "verify",
        },
        {
            "id": "r6", "agent": "technical-writer", "title": "Final compilation & polish", "phase": "deploy",
            "description": "Incorporates all feedback. Finalizes report, creates executive presentation. Delivers final package.",
            "inputs": ["Verification report", "Technical review notes", "Stakeholder feedback"],
            "outputs": ["Final report (.md)", "Executive presentation", "Source bibliography"],
            "depends_on": ["r5a", "r5b", "r5c"], "parallel_group": None,
        },
    ],
    "embedded-firmware": [
        {
            "id": "e1", "agent": "embedded-hardware-engineer", "title": "Pin planning & feasibility", "phase": "idea",
            "description": "Plans GPIO assignments, checks pin conflicts, verifies voltage levels, creates pinout diagram.",
            "inputs": ["Board specs", "Peripheral requirements"],
            "outputs": ["Pinout diagram", "Feasibility report"],
            "depends_on": [], "parallel_group": None,
        },
        {
            "id": "e2a", "agent": "embedded-firmware-engineer", "title": "HAL layer design", "phase": "requirements",
            "description": "Designs hardware abstraction layer interfaces for all peripherals (I2C, SPI, UART, GPIO, ADC).",
            "inputs": ["Pinout diagram"],
            "outputs": ["HAL interface headers", "Driver specifications"],
            "depends_on": ["e1"], "parallel_group": "hal",
        },
        {
            "id": "e2b", "agent": "embedded-sensor-driver-dev", "title": "Sensor driver prototyping", "phase": "requirements",
            "description": "Prototypes sensor-specific drivers. Tests communication protocols and data readout.",
            "inputs": ["Pinout diagram", "Sensor datasheets"],
            "outputs": ["Sensor driver prototypes", "Test readings"],
            "depends_on": ["e1"], "parallel_group": "hal",
        },
        {
            "id": "e3", "agent": "embedded-firmware-engineer", "title": "Business logic implementation", "phase": "design",
            "description": "Implements core firmware logic: state machines, data processing, control algorithms.",
            "inputs": ["HAL interface headers", "Sensor driver prototypes"],
            "outputs": ["Core firmware modules", "State machine diagrams"],
            "depends_on": ["e2a", "e2b"], "parallel_group": None,
        },
        {
            "id": "e4a", "agent": "embedded-testing-engineer", "title": "Unit & integration testing", "phase": "testing",
            "description": "Writes and runs unit tests for all modules. Integration tests on target hardware.",
            "inputs": ["Core firmware modules"],
            "outputs": ["Test reports", "Coverage data", "Bug tickets"],
            "depends_on": ["e3"], "parallel_group": "test",
        },
        {
            "id": "e4b", "agent": "embedded-iot-engineer", "title": "WiFi/Cloud integration", "phase": "testing",
            "description": "Implements WiFi connectivity, MQTT/HTTP data upload, OTA update capability.",
            "inputs": ["Core firmware modules"],
            "outputs": ["Connectivity module", "Cloud dashboard config"],
            "depends_on": ["e3"], "parallel_group": "test",
        },
        {
            "id": "e5", "agent": "embedded-firmware-engineer", "title": "Memory & power optimization", "phase": "implementation",
            "description": "Profiles RAM/Flash usage. Optimizes power consumption. Implements deep sleep modes.",
            "inputs": ["Test reports", "Core firmware modules"],
            "outputs": ["Optimized firmware build", "Power profile report"],
            "depends_on": ["e4a", "e4b"], "parallel_group": None,
        },
        {
            "id": "e6", "agent": "embedded-firmware-engineer", "title": "Flash & device validation", "phase": "deploy",
            "description": "Compiles final binary. Flashes to target device. Runs validation suite on hardware.",
            "inputs": ["Optimized firmware build"],
            "outputs": ["Production binary", "Validation report"],
            "depends_on": ["e5"], "parallel_group": None,
        },
    ],
    "web-fullstack": [
        {
            "id": "w1", "agent": "frontend-developer", "title": "UI/UX wireframes", "phase": "idea",
            "description": "Designs user flows, wireframes, and component hierarchy.",
            "inputs": ["Product requirements"],
            "outputs": ["Wireframes", "Component tree"],
            "depends_on": [], "parallel_group": None,
        },
        {
            "id": "w2a", "agent": "backend-developer", "title": "API design & data model", "phase": "requirements",
            "description": "Designs REST API contracts, database schema, and data flow.",
            "inputs": ["Product requirements"],
            "outputs": ["OpenAPI spec", "DB schema"],
            "depends_on": ["w1"], "parallel_group": "design",
        },
        {
            "id": "w2b", "agent": "software-architect", "title": "System architecture", "phase": "requirements",
            "description": "Defines system architecture, technology stack, deployment topology.",
            "inputs": ["Product requirements", "Wireframes"],
            "outputs": ["Architecture doc", "Tech stack decisions"],
            "depends_on": ["w1"], "parallel_group": "design",
        },
        {
            "id": "w3a", "agent": "frontend-developer", "title": "Frontend implementation", "phase": "implementation",
            "description": "Builds React components, pages, routing, and state management.",
            "inputs": ["Wireframes", "OpenAPI spec"],
            "outputs": ["Frontend build", "Component library"],
            "depends_on": ["w2a", "w2b"], "parallel_group": "build",
        },
        {
            "id": "w3b", "agent": "backend-developer", "title": "Backend implementation", "phase": "implementation",
            "description": "Implements API endpoints, database layer, authentication, and business logic.",
            "inputs": ["OpenAPI spec", "DB schema"],
            "outputs": ["API server", "DB migrations"],
            "depends_on": ["w2a", "w2b"], "parallel_group": "build",
        },
        {
            "id": "w4", "agent": "qa-engineer", "title": "Integration & E2E testing", "phase": "testing",
            "description": "Runs integration tests, E2E flows, API contract tests, and performance benchmarks.",
            "inputs": ["Frontend build", "API server"],
            "outputs": ["Test report", "Bug list", "Perf benchmarks"],
            "depends_on": ["w3a", "w3b"], "parallel_group": None,
        },
        {
            "id": "w5", "agent": "devops-engineer", "title": "CI/CD & deploy", "phase": "deploy",
            "description": "Sets up CI/CD pipeline, containerizes app, deploys to staging/production.",
            "inputs": ["Frontend build", "API server", "Test report"],
            "outputs": ["Deployed application", "CI/CD pipeline", "Monitoring setup"],
            "depends_on": ["w4"], "parallel_group": None,
        },
    ],
    "quick-prototype": [
        {
            "id": "q1", "agent": "rapid-prototyper", "title": "Scope MVP features", "phase": "idea",
            "description": "Identifies the minimum viable feature set. Cuts scope aggressively.",
            "inputs": ["Idea description"],
            "outputs": ["MVP scope doc"],
            "depends_on": [], "parallel_group": None,
        },
        {
            "id": "q2", "agent": "rapid-prototyper", "title": "Build core functionality", "phase": "implementation",
            "description": "Builds working prototype with the fastest possible path. No tests, no polish.",
            "inputs": ["MVP scope doc"],
            "outputs": ["Working prototype"],
            "depends_on": ["q1"], "parallel_group": None,
        },
        {
            "id": "q3", "agent": "qa-engineer", "title": "Smoke test", "phase": "testing",
            "description": "Quick smoke test of critical paths only. Flags showstopper bugs.",
            "inputs": ["Working prototype"],
            "outputs": ["Smoke test results", "Critical bugs"],
            "depends_on": ["q2"], "parallel_group": None,
        },
        {
            "id": "q4", "agent": "rapid-prototyper", "title": "Demo preparation", "phase": "deploy",
            "description": "Fixes critical bugs, prepares demo script, shares prototype with stakeholders.",
            "inputs": ["Smoke test results"],
            "outputs": ["Demo-ready prototype", "Demo script"],
            "depends_on": ["q3"], "parallel_group": None,
        },
    ],
    "embedded-linux": [
        {
            "id": "l1", "agent": "embedded-linux-engineer", "title": "Kernel config & BSP", "phase": "idea",
            "description": "Configures Linux kernel for target SoC. Creates board support package.",
            "inputs": ["Board specs", "SoC datasheet"],
            "outputs": ["Kernel .config", "Device tree", "BSP"],
            "depends_on": [], "parallel_group": None,
        },
        {
            "id": "l2a", "agent": "embedded-linux-engineer", "title": "Driver development", "phase": "design",
            "description": "Develops kernel drivers for target hardware peripherals.",
            "inputs": ["Device tree", "BSP"],
            "outputs": ["Kernel drivers", "Driver docs"],
            "depends_on": ["l1"], "parallel_group": "dev",
        },
        {
            "id": "l2b", "agent": "software-architect", "title": "Userspace architecture", "phase": "design",
            "description": "Designs userspace application architecture, IPC, and service layout.",
            "inputs": ["Board specs"],
            "outputs": ["App architecture doc"],
            "depends_on": ["l1"], "parallel_group": "dev",
        },
        {
            "id": "l3", "agent": "embedded-linux-engineer", "title": "Application development", "phase": "implementation",
            "description": "Implements userspace applications and services.",
            "inputs": ["Kernel drivers", "App architecture doc"],
            "outputs": ["Application binaries", "Startup scripts"],
            "depends_on": ["l2a", "l2b"], "parallel_group": None,
        },
        {
            "id": "l4", "agent": "embedded-testing-engineer", "title": "Cross-compile & integration test", "phase": "testing",
            "description": "Cross-compiles for target architecture. Runs integration tests on hardware.",
            "inputs": ["Application binaries", "Kernel drivers"],
            "outputs": ["Test report", "Root filesystem"],
            "depends_on": ["l3"], "parallel_group": None,
        },
        {
            "id": "l5", "agent": "devops-engineer", "title": "Image build & release", "phase": "deploy",
            "description": "Builds final system image (Buildroot/Yocto). Creates release artifacts.",
            "inputs": ["Root filesystem", "Test report"],
            "outputs": ["System image", "Release notes", "SDK"],
            "depends_on": ["l4"], "parallel_group": None,
        },
    ],
}

# ── routes ─────────────────────────────────────────────────────────────────────


@router.post("/", response_model=Idea, status_code=201)
async def create_idea(
    payload: IdeaCreate,
    session: AsyncSession = Depends(get_session),
) -> Idea:
    """Capture a new idea. Auto-creates a project if none provided."""
    project = ProjectModel(
        name=payload.title,
        description=payload.raw_description,
    )
    session.add(project)
    await session.flush()

    idea = IdeaModel(
        project_id=project.id,
        title=payload.title,
        raw_description=payload.raw_description,
        refined_description=payload.refined_description,
        suggested_pipeline=payload.suggested_pipeline,
        tags=json.dumps(payload.tags),
        status="new",
    )
    session.add(idea)
    await session.commit()
    await session.refresh(idea)

    return _model_to_idea(idea)


@router.get("/", response_model=PaginatedResponse)
async def list_ideas(
    project_id: str | None = None,
    status: str | None = None,
    limit: int = 200,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> PaginatedResponse:
    """List all ideas, optionally filtered by project or status. Paginated."""
    stmt = select(IdeaModel)
    if project_id:
        stmt = stmt.where(IdeaModel.project_id == project_id)
    if status:
        stmt = stmt.where(IdeaModel.status == status)
    stmt = stmt.order_by(IdeaModel.created_at.desc())
    return await paginate_query(
        session, stmt, IdeaModel, limit=limit, offset=offset,
        converter=_model_to_idea,
    )


@router.get("/{idea_id}", response_model=Idea)
async def get_idea(
    idea_id: str,
    session: AsyncSession = Depends(get_session),
) -> Idea:
    """Get a single idea by ID."""
    result = await session.execute(
        select(IdeaModel).where(IdeaModel.id == idea_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Idea not found")
    return _model_to_idea(model)


class RefinePayload(BaseModel):
    """Optional payload for the refine endpoint."""
    refined_description: str | None = None


@router.post("/{idea_id}/refine", response_model=Idea)
async def refine_idea(
    idea_id: str,
    payload: RefinePayload | None = None,
    session: AsyncSession = Depends(get_session),
) -> Idea:
    """Refine a raw idea — analyze and suggest pipeline + next steps.

    Optionally accepts a refined_description in the request body.
    """
    result = await session.execute(
        select(IdeaModel).where(IdeaModel.id == idea_id)
    )
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Heuristic pipeline suggestion with scoring, negative keywords, and tie-breaking
    desc_lower = idea.raw_description.lower()
    try:
        tags = json.loads(idea.tags) if isinstance(idea.tags, str) else idea.tags
    except (json.JSONDecodeError, TypeError):
        tags = []

    all_tags_lower = [t.lower() if isinstance(t, str) else t for t in tags]

    embedded_kw = ["m5stack", "esp32", "stm32", "arduino", "sensor", "motor",
                   "led", "gpio", "i2c", "spi", "firmware", "mcu", "rtos",
                   "embedded", "韌體", "嵌入式", "開發板"]
    linux_kw = ["linux", "kernel", "driver", "buildroot", "yocto",
                "raspberry", "beaglebone"]
    web_kw = ["web", "website", "dashboard", "api", "frontend", "backend",
              "react", "vue", "app", "網頁", "前端", "後端"]
    research_kw = ["分析", "分析報告", "report", "research", "研究", "市場",
                   "就業", "就業市場", "survey", "調研", "簡報", "文件"]

    # Negative keywords: if ANY appear, exclude that pipeline type
    embedded_negative = ["web", "frontend", "react", "vue", "api", "backend",
                         "純軟體", "software-only", "maintenance"]
    web_negative = ["embedded", "firmware", "mcu", "韌體", "硬體", "c++",
                    "c/c++", "sensor", "driver", "kernel"]
    linux_negative = ["arduino", "mcu", "單晶片", "sensor", "embedded"]

    def _score_pipeline(kw_list, negative_kw, tiebreaker):
        """Score a pipeline type. Higher = better match. Negative = exclusion.
        Tiebreaker only applies when at least one keyword matched."""
        score = 0
        for kw in kw_list:
            if kw in desc_lower:
                score += 2
        for t in all_tags_lower:
            if t in [kw.lower() for kw in kw_list]:
                score += 1
        # Negative keywords = instant exclusion
        for nkw in negative_kw:
            if nkw in desc_lower or nkw in all_tags_lower:
                return -999
        # Only add tiebreaker if there's at least one keyword match
        if score > 0:
            return score + tiebreaker
        return score  # 0 — no matches, don't inflate with tiebreaker

    scores = {
        "embedded-firmware": _score_pipeline(embedded_kw, embedded_negative, 5),
        "embedded-linux": _score_pipeline(linux_kw, linux_negative, 4),
        "web-fullstack": _score_pipeline(web_kw, web_negative, 3),
        "research-spike": _score_pipeline(research_kw, [], 2),
        "quick-prototype": _score_pipeline([], [], 1),
    }

    # Backend-only fallback: if the idea mentions only backend/Python with
    # NO frontend framework imports (react, vue, css, html), prefer quick-prototype
    backend_only = (
        any(kw in desc_lower for kw in ["backend", "python", "api", "fastapi"])
        and not any(kw in desc_lower for kw in ["react", "vue", "frontend",
                                                  "css", "html", "typescript",
                                                  "ui/ux", "wireframe"])
    )
    if backend_only and scores["web-fullstack"] > 0 and scores["quick-prototype"] < scores["web-fullstack"]:
        # Boost quick-prototype above web-fullstack when backend-only detected
        scores["quick-prototype"] = scores["web-fullstack"] + 1

    best = max(scores, key=scores.get)
    best_score = scores[best]
    suggested_pipeline = best if best_score > 0 else "quick-prototype"

    idea.suggested_pipeline = suggested_pipeline
    if payload and payload.refined_description:
        idea.refined_description = payload.refined_description
    idea.status = "refining"
    await session.commit()
    await session.refresh(idea)

    return _model_to_idea(idea)


@router.post("/{idea_id}/start")
async def start_idea(
    idea_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Bootstrap the full workflow: create pipeline, tasks, and team for an idea.

    This transitions the idea from 'refining' to 'in_progress' and generates
    everything needed to start executing.
    """
    result = await session.execute(
        select(IdeaModel).where(IdeaModel.id == idea_id)
    )
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Antibody guard: require refined_description before starting a pipeline
    if not idea.refined_description or not idea.refined_description.strip():
        raise HTTPException(
            status_code=400,
            detail=f"Idea '{idea.title}' has no refined description. "
                   f"Please refine the idea first via POST /api/ideas/{idea_id}/refine "
                   f"with a refined_description before starting a pipeline.",
        )

    pipeline_type = idea.suggested_pipeline or "quick-prototype"
    pipeline_def = _PIPELINE_DEFS.get(pipeline_type, _PIPELINE_DEFS["quick-prototype"])

    # Dynamic team composition: base team + gap analysis suggestions (top 3)
    base_team = [role.value if hasattr(role, "value") else str(role) for role in pipeline_def["team"]]
    gaps = _analyze_team_gaps(idea, None)
    extra_agents = [g["agent"] for g in gaps[:3] if g["agent"] not in base_team and g["relevance"] >= 2]
    final_team = base_team + extra_agents

    # 1. Create pipeline with steps
    now = datetime.now(timezone.utc).isoformat()
    steps = [
        {"phase": s["phase"], "name": s["name"],
         "agent": s["agent"].value if hasattr(s["agent"], "value") else s["agent"],
         "status": "todo"}
        for s in pipeline_def["phases"]
    ]
    pipeline = PipelineModel(
        project_id=idea.project_id,
        pipeline_type=pipeline_type,
        idea_id=idea.id,
        steps=json.dumps(steps),
        current_phase=steps[0]["phase"],
    )
    session.add(pipeline)
    await session.flush()

    # 2. Build description for a pipeline seed task
    def _build_task_description(title: str, agent: str) -> str:
        """Populate a meaningful task description.
        Priority:
          1. Match the task title to an agent workflow step and use its description,
             prefixed with the idea refined_description as context.
          2. If no workflow match, use refined_description + template.
          3. Fall back to a generic template with pipeline type and agent role.
        """
        if idea.refined_description and idea.refined_description.strip():
            ctx = f"Project context: {idea.refined_description.strip()[:400]}"
            # Try matching to a workflow step description
            workflow = _AGENT_WORKFLOWS.get(pipeline_type, [])
            for step in workflow:
                step_title_lower = step["title"].lower()
                title_lower = title.lower()
                # Match if the step title appears in the task title or vice versa
                if step_title_lower in title_lower or title_lower in step_title_lower:
                    step_desc = step.get("description", "").strip()
                    if step_desc:
                        return f"{ctx}\n\nGoal: {step_desc}"
            # No workflow match — use refined_description directly
            return f"{ctx}\n\nDeliverable: {title}"
        # No refined_description — use a template based on pipeline step + agent
        return f"Pipeline: {pipeline_type} | Phase task: {title} | Agent: {agent}"

    # 2. Create seed tasks (assigned cyclically across the dynamic team)
    tasks_created = []
    for i, task_title in enumerate(pipeline_def["seed_tasks"]):
        agent = final_team[i % len(final_team)] if final_team else "unassigned"
        task = TaskModel(
            project_id=idea.project_id,
            title=task_title,
            description=_build_task_description(task_title, agent),
            status="todo",
            priority="high" if i == 0 else "medium",
            assigned_agent=agent,
        )
        session.add(task)
        tasks_created.append(task)

    # 3. Create team (dynamically composed: base team + gap-filling agents)
    member_list = [
        {"role": role, "status": "idle"}
        for role in final_team
    ]
    team = TeamModel(
        name=f"Team for: {idea.title}",
        project_id=idea.project_id,
        members=json.dumps(member_list),
    )
    session.add(team)

    # 4. Update idea status
    idea.status = "in_progress"
    await session.commit()
    await session.refresh(idea)

    return {
        "idea": _model_to_idea(idea).model_dump(),
        "pipeline": {
            "id": pipeline.id,
            "pipeline_type": pipeline_type,
            "current_phase": pipeline.current_phase,
            "steps": steps,
        },
        "tasks": [
            {"id": t.id, "title": t.title, "status": t.status,
             "priority": t.priority, "assigned_agent": t.assigned_agent}
            for t in tasks_created
        ],
        "team": {
            "id": team.id,
            "name": team.name,
            "members": member_list,
        },
    }


@router.get("/{idea_id}/workflow")
async def get_idea_workflow(
    idea_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get the full workflow state for an idea: pipeline, tasks, and team."""
    result = await session.execute(
        select(IdeaModel).where(IdeaModel.id == idea_id)
    )
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Pipeline
    pipeline_result = await session.execute(
        select(PipelineModel).where(PipelineModel.idea_id == idea_id)
    )
    pipeline_model = pipeline_result.scalar_one_or_none()

    pipeline_data = None
    if pipeline_model:
        try:
            steps = json.loads(pipeline_model.steps) if pipeline_model.steps else []
        except json.JSONDecodeError:
            steps = []
        pipeline_data = {
            "id": pipeline_model.id,
            "pipeline_type": pipeline_model.pipeline_type,
            "current_phase": pipeline_model.current_phase,
            "steps": steps,
            "created_at": pipeline_model.created_at.isoformat() if pipeline_model.created_at else None,
        }

    # Tasks
    tasks_result = await session.execute(
        select(TaskModel)
        .where(TaskModel.project_id == idea.project_id)
        .order_by(TaskModel.created_at.asc())
    )
    task_list = tasks_result.scalars().all()
    tasks_data = [
        {
            "id": t.id, "title": t.title, "status": t.status,
            "priority": t.priority, "assigned_agent": t.assigned_agent,
        }
        for t in task_list
    ]

    # Team
    team_result = await session.execute(
        select(TeamModel).where(TeamModel.project_id == idea.project_id)
    )
    team_model = team_result.scalar_one_or_none()

    team_data = None
    if team_model:
        try:
            members = json.loads(team_model.members) if team_model.members else []
        except json.JSONDecodeError:
            members = []
        team_data = {
            "id": team_model.id,
            "name": team_model.name,
            "members": members,
        }

    # Auto-sync: align idea status with actual pipeline + task state
    if pipeline_model and task_list:
        all_done = all(t.status == "done" for t in task_list)
        any_progress = any(t.status in ("done", "in_progress") for t in task_list)

        if pipeline_model.current_phase == "done" and all_done:
            if idea.status != "done":
                idea.status = "done"
                await session.commit()
                await session.refresh(idea)
        elif idea.status == "done" and not all_done:
            # Stale "done" status — tasks not actually done, roll back
            idea.status = "in_progress"
            await session.commit()
            await session.refresh(idea)

    # Team gap analysis: what skills does this idea need that the current team lacks?
    team_gaps = _analyze_team_gaps(idea, team_model)

    # Agent workflow
    agent_workflow = None
    if pipeline_model and pipeline_model.pipeline_type in _AGENT_WORKFLOWS:
        agent_workflow = _AGENT_WORKFLOWS[pipeline_model.pipeline_type]
        # Mark action status based on pipeline phase
        current_phase = pipeline_model.current_phase
        phase_order = ["idea", "requirements", "design", "implementation", "testing", "deploy", "done"]
        current_phase_idx = phase_order.index(current_phase) if current_phase in phase_order else 0

        for action in agent_workflow:
            action_phase_idx = phase_order.index(action.get("phase", "idea")) if action.get("phase", "idea") in phase_order else 0
            if action_phase_idx < current_phase_idx:
                action["status"] = "done"
            elif action_phase_idx == current_phase_idx:
                action["status"] = "in_progress" if current_phase != "done" else "done"
            else:
                action["status"] = "pending"

    return {
        "idea": _model_to_idea(idea).model_dump(),
        "pipeline": pipeline_data,
        "tasks": tasks_data,
        "team": team_data,
        "agent_workflow": agent_workflow,
        "team_gaps": team_gaps,
    }


@router.get("/{idea_id}/deliverables")
async def list_deliverables(idea_id: str) -> list[dict]:
    """List deliverables (files) generated for an idea."""
    from pathlib import Path

    deliverables_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "deliverables"
    if not deliverables_dir.exists():
        return []

    files = []
    for f in sorted(deliverables_dir.glob(f"{idea_id}*"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        files.append({
            "name": f.name,
            "path": str(f.relative_to(deliverables_dir.parent)),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "preview": f.read_text(encoding="utf-8")[:2000] if f.suffix in (".md", ".txt", ".json") else None,
        })

    return files


@router.get("/{idea_id}/deliverables/{filename:path}/html")
async def get_deliverable_html(idea_id: str, filename: str):
    """Serve a deliverable file rendered as a styled HTML page. MUST be before the catch-all {filename:path} route."""
    from fastapi.responses import HTMLResponse

    file_path = _resolve_deliverable_path(filename)
    if file_path is None or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    md_content = file_path.read_text(encoding="utf-8")
    html_body = _markdown_to_html(md_content)
    html_page = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{file_path.name}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans TC', sans-serif;
    background: #0d1117; color: #c9d1d9; line-height: 1.7;
    max-width: 860px; margin: 0 auto; padding: 40px 24px;
  }}
  h1 {{ font-size: 2em; color: #58a6ff; border-bottom: 1px solid #21262d; padding-bottom: 12px; margin-bottom: 8px; }}
  h2 {{ font-size: 1.4em; color: #f0f6fc; margin-top: 36px; margin-bottom: 12px; border-bottom: 1px solid #21262d; padding-bottom: 6px; }}
  h3 {{ font-size: 1.15em; color: #f0f6fc; margin-top: 24px; margin-bottom: 8px; }}
  h4 {{ font-size: 1em; color: #f0f6fc; margin-top: 18px; margin-bottom: 6px; }}
  p {{ margin: 10px 0; }}
  strong {{ color: #f0f6fc; }}
  blockquote {{ border-left: 3px solid #58a6ff; padding: 8px 16px; margin: 16px 0; color: #8b949e; background: #161b22; border-radius: 0 6px 6px 0; }}
  blockquote p {{ margin: 4px 0; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  code {{ background: #161b22; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; color: #f0883e; }}
  pre {{ background: #161b22; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; }}
  pre code {{ background: none; padding: 0; color: #c9d1d9; }}
  ul, ol {{ padding-left: 24px; margin: 10px 0; }}
  li {{ margin: 4px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
  th {{ background: #161b22; padding: 10px 14px; text-align: left; font-weight: 600; border-bottom: 2px solid #30363d; color: #f0f6fc; }}
  td {{ padding: 8px 14px; border-bottom: 1px solid #21262d; }}
  tr:hover td {{ background: #161b22; }}
  hr {{ border: none; border-top: 1px solid #21262d; margin: 32px 0; }}
  img {{ max-width: 100%; border-radius: 6px; }}
  .deliverable-meta {{
    background: #161b22; border: 1px solid #21262d; border-radius: 8px;
    padding: 16px 20px; margin-bottom: 32px; font-size: 0.9em; color: #8b949e;
  }}
  .deliverable-meta strong {{ color: #c9d1d9; }}
</style>
</head>
<body>
<div class="deliverable-meta">
  <strong>Deliverable:</strong> {file_path.name}<br>
  <strong>Size:</strong> {file_path.stat().st_size / 1024:.1f} KB &nbsp;|&nbsp;
  <strong>Generated:</strong> {datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
</div>
{html_body}
</body>
</html>"""
    return HTMLResponse(content=html_page)


@router.get("/{idea_id}/deliverables/{filename:path}")
async def get_deliverable_content(idea_id: str, filename: str) -> dict:
    """Serve a deliverable file's full content. Catch-all — keep AFTER /html route."""
    file_path = _resolve_deliverable_path(filename)
    if file_path is None or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "name": file_path.name,
        "content": file_path.read_text(encoding="utf-8"),
        "size": file_path.stat().st_size,
    }


# ── Team Management ────────────────────────────────────────────────────────────


@router.post("/{idea_id}/team/add-agent")
async def add_agent_to_team(
    idea_id: str,
    agent_role: str = "",
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Dynamically add an agent to the idea's team."""
    result = await session.execute(select(IdeaModel).where(IdeaModel.id == idea_id))
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    team_result = await session.execute(
        select(TeamModel).where(TeamModel.project_id == idea.project_id)
    )
    team = team_result.scalar_one_or_none()

    members = json.loads(team.members) if team and team.members else []
    existing = [m["role"] for m in members]

    if agent_role in existing:
        return {"status": "already_present", "agent": agent_role, "message": f"{agent_role} is already in the team."}

    if agent_role not in _AGENT_SKILLS:
        return {"status": "unknown_agent", "agent": agent_role, "valid_agents": sorted(_AGENT_SKILLS.keys())}

    members.append({"role": agent_role, "status": "idle"})
    team.members = json.dumps(members)
    await session.commit()

    return {
        "status": "added",
        "agent": agent_role,
        "team_size": len(members),
        "message": f"Added {agent_role} to the team. Team now has {len(members)} members.",
    }


@router.post("/{idea_id}/team/remove-agent")
async def remove_agent_from_team(
    idea_id: str,
    agent_role: str = "",
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Remove an agent from the idea's team."""
    result = await session.execute(select(IdeaModel).where(IdeaModel.id == idea_id))
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    team_result = await session.execute(
        select(TeamModel).where(TeamModel.project_id == idea.project_id)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        return {"status": "no_team", "message": "No team exists for this idea yet."}

    members = json.loads(team.members) if team.members else []
    members = [m for m in members if m["role"] != agent_role]
    team.members = json.dumps(members)
    await session.commit()

    return {"status": "removed", "agent": agent_role, "team_size": len(members)}


@router.patch("/{idea_id}/archive")
async def archive_idea(
    idea_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Archive an idea — hides it from the dashboard but keeps data in DB."""
    result = await session.execute(
        select(IdeaModel).where(IdeaModel.id == idea_id)
    )
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    idea.status = "archived"
    await session.commit()

    return {"status": "archived", "title": idea.title, "id": idea_id}


# ── file helpers ───────────────────────────────────────────────────────────────


def _analyze_team_gaps(idea: IdeaModel, team_model) -> list[dict]:
    """Analyze what skills an idea needs that the current team lacks.

    Returns a list of suggested agents to add, with rationale.
    """
    if not idea or not idea.raw_description:
        return []

    desc = idea.raw_description.lower()
    try:
        tags = json.loads(idea.tags) if isinstance(idea.tags, str) else (idea.tags or [])
    except (json.JSONDecodeError, TypeError):
        tags = []
    all_text = desc + " " + " ".join(t.lower() for t in tags if isinstance(t, str))

    # Current team members
    current_agents: set[str] = set()
    if team_model and team_model.members:
        try:
            members = json.loads(team_model.members) if isinstance(team_model.members, str) else team_model.members
            current_agents = {m["role"] for m in members}
        except (json.JSONDecodeError, TypeError):
            pass

    # Default pipeline team if no team model yet
    if not current_agents and idea.suggested_pipeline and idea.suggested_pipeline in _PIPELINE_DEFS:
        pipeline_def = _PIPELINE_DEFS[idea.suggested_pipeline]
        current_agents = {role.value if hasattr(role, "value") else str(role) for role in pipeline_def.get("team", [])}

    # Score each agent against the idea text
    scored: list[tuple[str, int, list[str]]] = []
    for agent_id, data in _AGENT_SKILLS.items():
        if agent_id in current_agents:
            continue  # Already on team

        matched_skills: list[str] = []
        for skill in data["skills"]:
            if skill.replace("-", " ") in all_text or skill in all_text:
                matched_skills.append(skill)
        for kw in data["keywords"]:
            if kw in all_text:
                matched_skills.append(kw)

        if matched_skills:
            scored.append((agent_id, len(matched_skills), list(set(matched_skills))))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "agent": agent_id,
            "relevance": score,
            "matched_skills": matched,
            "rationale": f"This idea mentions concepts ({', '.join(matched[:3])}) that match {agent_id}'s expertise. Consider adding to the team.",
        }
        for agent_id, score, matched in scored[:5]
    ]


def _resolve_deliverable_path(filename: str):
    from pathlib import Path

    deliverables_root = (Path(__file__).parent.parent.parent.parent.parent / "data" / "deliverables").resolve()
    file_path = (deliverables_root / filename).resolve()
    if not str(file_path).startswith(str(deliverables_root)):
        return None
    return file_path if file_path.exists() and file_path.is_file() else None


def _markdown_to_html(md: str) -> str:
    """Simple markdown-to-HTML converter."""
    import re

    lines = md.split('\n')
    out = []
    in_code_block = False
    in_table = False
    in_list = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            if in_code_block:
                out.append('</code></pre>')
                in_code_block = False
            else:
                out.append('<pre><code>')
                in_code_block = True
            i += 1
            continue
        if in_code_block:
            out.append(_escape_html(line))
            i += 1
            continue

        # Table
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                in_table = True
                out.append('<table>')
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            # Check for separator row
            if all(re.match(r'^[-:]+$', c) for c in cells):
                i += 1
                continue
            tag = 'th' if in_table and (i + 1 < len(lines) and '|' in lines[i + 1] and all(re.match(r'^[-:]+$', c.strip()) for c in lines[i + 1].strip().strip('|').split('|'))) else 'td'
            if tag == 'th':
                out.append('<tr>' + ''.join(f'<th>{_inline_md(c)}</th>' for c in cells) + '</tr>')
            else:
                out.append('<tr>' + ''.join(f'<td>{_inline_md(c)}</td>' for c in cells) + '</tr>')
            # If next line not a table row, close table
            if i + 1 >= len(lines) or '|' not in lines[i + 1]:
                out.append('</table>')
                in_table = False
            i += 1
            continue

        if in_table:
            out.append('</table>')
            in_table = False

        # Headings
        h_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if h_match:
            level = len(h_match.group(1))
            out.append(f'<h{level}>{_inline_md(h_match.group(2))}</h{level}>')
            i += 1
            continue

        # Blockquote
        if line.startswith('> '):
            bq_lines = []
            while i < len(lines) and lines[i].startswith('> '):
                bq_lines.append(lines[i][2:])
                i += 1
            bq_body = _markdown_to_html('\n'.join(bq_lines))
            out.append(f'<blockquote>{bq_body}</blockquote>')
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}$', line.strip()):
            out.append('<hr>')
            i += 1
            continue

        # Unordered list
        ul_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if ul_match:
            if not in_list or in_list != 'ul':
                if in_list: out.append(f'</{in_list}>')
                out.append('<ul>')
                in_list = 'ul'
            out.append(f'<li>{_inline_md(ul_match.group(2))}</li>')
            i += 1
            # If next line is not a list item, close
            if i >= len(lines) or not re.match(r'^(\s*)[-*+]\s+', lines[i]):
                out.append('</ul>')
                in_list = False
            continue

        # Ordered list
        ol_match = re.match(r'^(\s*)\d+[.)]\s+(.+)$', line)
        if ol_match:
            if not in_list or in_list != 'ol':
                if in_list: out.append(f'</{in_list}>')
                out.append('<ol>')
                in_list = 'ol'
            out.append(f'<li>{_inline_md(ol_match.group(2))}</li>')
            i += 1
            if i >= len(lines) or not re.match(r'^(\s*)\d+[.)]\s+', lines[i]):
                out.append('</ol>')
                in_list = False
            continue

        # Close any open list on blank line
        if in_list and line.strip() == '':
            out.append(f'</{in_list}>')
            in_list = False
            i += 1
            continue

        # Paragraph (non-empty)
        if line.strip():
            para_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') and not lines[i].startswith('>') and not lines[i].startswith('```') and not re.match(r'^[-*+]\s+', lines[i]) and not re.match(r'^\d+[.)]\s+', lines[i]) and not (in_table and '|' in lines[i]):
                para_lines.append(lines[i])
                i += 1
            out.append(f'<p>{" ".join(_inline_md(l) for l in para_lines)}</p>')
            continue

        i += 1

    if in_code_block: out.append('</code></pre>')
    if in_table: out.append('</table>')
    if in_list: out.append(f'</{in_list}>')

    return '\n'.join(out)


def _inline_md(text: str) -> str:
    """Convert inline markdown to HTML."""
    import re
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def _escape_html(text: str) -> str:
    """Escape HTML special chars."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ── helpers ────────────────────────────────────────────────────────────────────


def _model_to_idea(m: IdeaModel) -> Idea:
    """Convert ORM model to Pydantic schema."""
    try:
        tags = json.loads(m.tags) if isinstance(m.tags, str) else m.tags
    except (json.JSONDecodeError, TypeError):
        tags = []
    return Idea(
        id=m.id,
        title=m.title,
        raw_description=m.raw_description,
        tags=tags or [],
        refined_description=m.refined_description,
        suggested_pipeline=m.suggested_pipeline,
        status=m.status,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )
