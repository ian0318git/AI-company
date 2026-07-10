"""MCP tools for idea capture and refinement."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ai_embedded_company.mcp._base import _api_call, _resolve_project_id
from ai_embedded_company.storage.database import _get_sessionmaker
from ai_embedded_company.storage.models import IdeaModel, ProjectModel


def register_tools(mcp):
    """Register idea tools with the FastMCP instance."""

    @mcp.tool()
    async def idea_capture(
        title: str,
        description: str,
        project_id: str = "",
        tags: str = "",
    ) -> dict:
        """Capture a raw idea into the system.

        This is the entry point for any new idea. The idea will be stored
        and can later be refined, turned into a pipeline, and built.

        Args:
            title: Short title for the idea (e.g., "M5Stack 溫濕度監測器")
            description: Raw description — can be vague, stream-of-consciousness
            project_id: Optional project UUID. Creates a new project if empty.
            tags: Comma-separated tags (e.g., "m5stack,sensor,iot")
        """
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        # If no project_id, auto-create a project for this idea
        if not project_id:
            proj = await _api_call("POST", "/api/projects/", json_data={
                "name": title,
                "description": description,
            })
            project_id = proj.get("id", "")

        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            idea = IdeaModel(
                project_id=project_id,
                title=title,
                raw_description=description,
                tags=json.dumps(tag_list),
                status="new",
            )
            session.add(idea)
            await session.commit()
            await session.refresh(idea)

            return {
                "idea_id": idea.id,
                "title": title,
                "project_id": project_id,
                "tags": tag_list,
                "status": "new",
                "message": f"Idea captured. Next: use idea_refine to expand this into requirements, or pipeline_create to start building immediately.",
            }

    @mcp.tool()
    async def idea_refine(idea_id: str) -> dict:
        """Refine a raw idea into structured requirements.

        This analyzes the idea description and suggests:
        - A refined problem statement
        - Recommended pipeline type
        - MVP scope suggestions
        - Technical requirements
        - First actionable task

        Args:
            idea_id: The idea UUID from idea_capture
        """
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(IdeaModel).where(IdeaModel.id == idea_id)
            )
            idea = result.scalar_one_or_none()

            if idea is None:
                return {"error": f"Idea not found: {idea_id}"}

            # Auto-suggest pipeline type based on tags and description
            desc_lower = idea.raw_description.lower()
            tags_raw = idea.tags
            try:
                tags = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
            except (json.JSONDecodeError, TypeError):
                tags = []

            # Heuristic pipeline suggestion with scoring and tie-breaking
            # Each keyword group scores +2 per description match, +1 per tag match.
            # Negative keyword matches score -5 (exclusion override).
            # Wider/broader categories get lower tiebreaker priority.

            embedded_kw = ["m5stack", "esp32", "stm32", "arduino", "sensor", "motor", "led", "gpio", "i2c", "spi", "firmware", "mcu", "rtos", "embedded", "韌體", "嵌入式", "開發板"]
            linux_kw = ["linux", "kernel", "driver", "buildroot", "yocto", "raspberry", "beaglebone"]
            web_kw = ["web", "website", "dashboard", "api", "frontend", "backend", "react", "vue", "app", "網頁", "前端", "後端"]
            research_kw = ["分析", "分析報告", "report", "research", "研究", "市場", "就業", "就業市場", "survey", "調研", "簡報", "文件"]

            # Negative keywords: if ANY of these appear in description/tags, exclude the pipeline type
            embedded_negative = ["web", "frontend", "react", "vue", "api", "backend", "純軟體", "software-only", "maintenance"]
            web_negative = ["embedded", "firmware", "mcu", "韌體", "硬體", "c++", "c/c++"]
            linux_negative = ["embedded", "arduino", "mcu", "單晶片", "sensor"]

            def _score_pipeline(kw_list: list[str], negative_kw: list[str], tiebreaker: int) -> int:
                """Score a pipeline type. Higher = better match.

                Tiebreaker is only added when at least one keyword matches.
                If no keyword matches at all, score is 0 (not tiebreaker).
                """
                score = 0
                for kw in kw_list:
                    if kw in desc_lower:
                        score += 2
                for t in tags:
                    t_lower = t.lower() if isinstance(t, str) else t
                    if t_lower in [kw.lower() for kw in kw_list]:
                        score += 1
                # Negative keywords = instant exclusion
                for nkw in negative_kw:
                    if nkw in desc_lower or any(
                        (t.lower() if isinstance(t, str) else t) == nkw.lower()
                        for t in tags
                    ):
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
                "quick-prototype": _score_pipeline([], [], 1),  # baseline 1pt
            }

            # Pick highest-scoring pipeline type
            best = max(scores, key=scores.get)
            best_score = scores[best]
            suggested_pipeline = best if best_score > 0 else "quick-prototype"

            # Update the idea
            idea.suggested_pipeline = suggested_pipeline
            idea.status = "refining"
            await session.commit()

            return {
                "idea_id": idea.id,
                "title": idea.title,
                "project_id": idea.project_id,
                "raw_description": idea.raw_description,
                "suggested_pipeline": suggested_pipeline,
                "status": "refining",
                "recommendation": _get_pipeline_rationale(suggested_pipeline, idea.title),
                "next_steps": [
                    f"1. Use pipeline_create with pipeline_type='{suggested_pipeline}' and project_id='{idea.project_id}'",
                    "2. The pipeline will generate specific tasks based on the idea",
                    "3. Use task_wall to view and manage the generated tasks",
                ],
            }

    @mcp.tool()
    async def idea_list(project_id: str = "", status: str = "") -> dict:
        """List all captured ideas.

        Args:
            project_id: Filter by project UUID (optional)
            status: Filter by status: new, refining, approved, rejected, in_progress, done
        """
        sessionmaker = _get_sessionmaker()
        async with sessionmaker() as session:
            from sqlalchemy import select

            stmt = select(IdeaModel)
            if project_id:
                stmt = stmt.where(IdeaModel.project_id == project_id)
            if status:
                stmt = stmt.where(IdeaModel.status == status)
            stmt = stmt.order_by(IdeaModel.created_at.desc())

            result = await session.execute(stmt)
            ideas = result.scalars().all()

            return {
                "ideas": [
                    {
                        "id": i.id,
                        "title": i.title,
                        "project_id": i.project_id,
                        "status": i.status,
                        "suggested_pipeline": i.suggested_pipeline,
                        "created_at": i.created_at.isoformat() if i.created_at else None,
                    }
                    for i in ideas
                ]
            }


def _get_pipeline_rationale(pipeline_type: str, title: str) -> str:
    """Return a human-readable rationale for the pipeline suggestion."""
    rationales = {
        "embedded-firmware": (
            f"'{title}' 看起來是嵌入式韌體專案。建議使用 embedded-firmware pipeline：\n"
            "Idea → 腳位規劃 → HAL 層 → 業務邏輯 → 測試 → 燒錄到開發板。\n"
            "這條 pipeline 會自動分配 Firmware Engineer 和 Hardware Engineer。"
        ),
        "embedded-linux": (
            f"'{title}' 需要 Linux 系統功能。建議使用 embedded-linux pipeline：\n"
            "Idea → 系統設計 → Driver/App 開發 → 交叉編譯 → 測試。\n"
            "適合需要完整 OS 支援的專案 (相機、複雜網路、GUI)。"
        ),
        "web-fullstack": (
            f"'{title}' 適合 Web 全端開發。建議使用 web-fullstack pipeline：\n"
            "Idea → UI/UX 設計 → Frontend → Backend → 部署。\n"
            "會產出前後端分離的完整應用。"
        ),
        "quick-prototype": (
            f"'{title}' 建議先用 quick-prototype pipeline 快速驗證：\n"
            "Idea → MVP → 迭代。用最快路徑做出能跑的原型，確認方向後再重構。"
        ),
    }
    return rationales.get(
        pipeline_type,
        f"'{title}' 已擷取。請使用 pipeline_create 選擇合適的 pipeline 類型開始開發。",
    )
