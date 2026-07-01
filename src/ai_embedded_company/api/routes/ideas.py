"""Idea capture, retrieval, refinement, and workflow bootstrap routes."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_embedded_company.storage import get_session
from ai_embedded_company.storage.models import (
    IdeaModel,
    PipelineModel,
    ProjectModel,
    TaskModel,
    TeamModel,
)
from ai_embedded_company.types import AgentRole, Idea, IdeaCreate

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
        tags=json.dumps(payload.tags),
        status="new",
    )
    session.add(idea)
    await session.commit()
    await session.refresh(idea)

    return _model_to_idea(idea)


@router.get("/", response_model=list[Idea])
async def list_ideas(
    project_id: str | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Idea]:
    """List all ideas, optionally filtered by project or status."""
    stmt = select(IdeaModel)
    if project_id:
        stmt = stmt.where(IdeaModel.project_id == project_id)
    if status:
        stmt = stmt.where(IdeaModel.status == status)
    stmt = stmt.order_by(IdeaModel.created_at.desc())
    result = await session.execute(stmt)
    models = result.scalars().all()
    return [_model_to_idea(m) for m in models]


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


@router.post("/{idea_id}/refine", response_model=Idea)
async def refine_idea(
    idea_id: str,
    session: AsyncSession = Depends(get_session),
) -> Idea:
    """Refine a raw idea — analyze and suggest pipeline + next steps."""
    result = await session.execute(
        select(IdeaModel).where(IdeaModel.id == idea_id)
    )
    idea = result.scalar_one_or_none()
    if idea is None:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Heuristic pipeline suggestion
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

    is_embedded = any(kw in desc_lower for kw in embedded_kw) or any(
        t in [kw.lower() for kw in embedded_kw] for t in all_tags_lower)
    is_linux = any(kw in desc_lower for kw in linux_kw) or any(
        t in [kw.lower() for kw in linux_kw] for t in all_tags_lower)
    is_web = any(kw in desc_lower for kw in web_kw) or any(
        t in [kw.lower() for kw in web_kw] for t in all_tags_lower)
    is_research = any(kw in desc_lower for kw in research_kw) or any(
        t in [kw.lower() for kw in research_kw] for t in all_tags_lower)

    if is_research:
        suggested_pipeline = "research-spike"
    elif is_linux:
        suggested_pipeline = "embedded-linux"
    elif is_embedded:
        suggested_pipeline = "embedded-firmware"
    elif is_web:
        suggested_pipeline = "web-fullstack"
    else:
        suggested_pipeline = "quick-prototype"

    idea.suggested_pipeline = suggested_pipeline
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

    pipeline_type = idea.suggested_pipeline or "quick-prototype"
    pipeline_def = _PIPELINE_DEFS.get(pipeline_type, _PIPELINE_DEFS["quick-prototype"])

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

    # 2. Create seed tasks
    tasks_created = []
    for i, task_title in enumerate(pipeline_def["seed_tasks"]):
        task = TaskModel(
            project_id=idea.project_id,
            title=task_title,
            description="",
            status="todo",
            priority="high" if i == 0 else "medium",
            assigned_agent=pipeline_def["team"][i % len(pipeline_def["team"])].value
            if pipeline_def["team"] else None,
        )
        session.add(task)
        tasks_created.append(task)

    # 3. Create team
    member_list = [
        {"role": role.value if hasattr(role, "value") else role, "status": "idle"}
        for role in pipeline_def["team"]
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

    return {
        "idea": _model_to_idea(idea).model_dump(),
        "pipeline": pipeline_data,
        "tasks": tasks_data,
        "team": team_data,
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


# ── file helpers ───────────────────────────────────────────────────────────────


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
