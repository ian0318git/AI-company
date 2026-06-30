"""MCP tools for pipeline orchestration."""

from __future__ import annotations

import json

from ai_embedded_company.mcp._base import _api_call, _resolve_project_id
from ai_embedded_company.types import PipelinePhase, PipelineType


# ── Pipeline Template Definitions ────────────────────────────────────────────

PIPELINE_TEMPLATES = {
    "embedded-firmware": {
        "name": "Embedded Firmware Pipeline",
        "description": "從想法到燒錄的完整 MCU 韌體開發流程",
        "phases": [
            {"phase": "idea", "name": "需求分析", "agent": "idea-refiner",
             "description": "分析需求，產出功能規格與腳位規劃"},
            {"phase": "requirements", "name": "腳位規劃與硬體確認", "agent": "embedded-hardware-engineer",
             "description": "確認所有腳位、電源、周邊連接無衝突"},
            {"phase": "design", "name": "HAL 層架構設計", "agent": "embedded-firmware-engineer",
             "description": "設計硬體抽象層，定義驅動介面"},
            {"phase": "implementation", "name": "業務邏輯實作", "agent": "embedded-firmware-engineer",
             "description": "實作核心功能邏輯"},
            {"phase": "testing", "name": "測試與驗證", "agent": "embedded-testing-engineer",
             "description": "單元測試 + 硬體測試 + 記憶體/功耗分析"},
            {"phase": "deploy", "name": "燒錄與驗收", "agent": "embedded-testing-engineer",
             "description": "燒錄韌體到開發板，驗證所有功能"},
        ],
    },
    "embedded-linux": {
        "name": "Embedded Linux Pipeline",
        "description": "從需求到 Embedded Linux 系統部署",
        "phases": [
            {"phase": "idea", "name": "需求分析", "agent": "idea-refiner",
             "description": "分析需求，確認是否需要 Linux 功能"},
            {"phase": "requirements", "name": "系統設計", "agent": "embedded-linux-engineer",
             "description": "設計系統架構、選擇 BSP、規劃分割區"},
            {"phase": "design", "name": "Driver/Device Tree", "agent": "embedded-linux-engineer",
             "description": "撰寫 Device Tree、Kernel 驅動"},
            {"phase": "implementation", "name": "應用程式開發", "agent": "backend-developer",
             "description": "開發用戶空間應用程式"},
            {"phase": "testing", "name": "交叉編譯與測試", "agent": "embedded-testing-engineer",
             "description": "交叉編譯、QEMU 測試、目標硬體測試"},
        ],
    },
    "web-fullstack": {
        "name": "Web Fullstack Pipeline",
        "description": "從想法到部署的完整 Web 應用開發流程",
        "phases": [
            {"phase": "idea", "name": "需求分析", "agent": "idea-refiner",
             "description": "分析需求，定義使用者故事"},
            {"phase": "requirements", "name": "UI/UX 設計", "agent": "frontend-developer",
             "description": "設計頁面結構與使用者流程"},
            {"phase": "design", "name": "API/資料庫設計", "agent": "backend-developer",
             "description": "設計 API 合約與資料模型"},
            {"phase": "implementation", "name": "前後端實作", "agent": "fullstack-developer",
             "description": "實作前端頁面與後端 API"},
            {"phase": "testing", "name": "整合測試", "agent": "qa-engineer",
             "description": "E2E 測試、API 測試、效能測試"},
            {"phase": "deploy", "name": "部署上線", "agent": "devops-engineer",
             "description": "Docker 化、CI/CD、部署到伺服器"},
        ],
    },
    "quick-prototype": {
        "name": "Quick Prototype Pipeline",
        "description": "最快路徑做出能跑的原型，驗證想法",
        "phases": [
            {"phase": "idea", "name": "釐清核心價值", "agent": "idea-refiner",
             "description": "找出 MVP 的最小範圍"},
            {"phase": "implementation", "name": "快速實作 MVP", "agent": "rapid-prototyper",
             "description": "用最快方式做出能跑的原型"},
            {"phase": "testing", "name": "驗證與回顧", "agent": "tech-lead",
             "description": "評估原型：值得繼續投入嗎？需要轉換 pipeline 嗎？"},
        ],
    },
    "research-spike": {
        "name": "Research Spike Pipeline",
        "description": "技術調研：回答一個技術問題，產出可行性報告",
        "phases": [
            {"phase": "idea", "name": "定義研究問題", "agent": "tech-lead",
             "description": "精確定義要研究什麼、成功標準是什麼"},
            {"phase": "requirements", "name": "文獻與競品調研", "agent": "software-architect",
             "description": "搜尋現有方案、類似實作、相關文件"},
            {"phase": "design", "name": "可行性分析", "agent": "software-architect",
             "description": "評估技術可行性、資源需求、風險"},
            {"phase": "testing", "name": "概念驗證 (PoC)", "agent": "rapid-prototyper",
             "description": "最小可行實驗，驗證核心假設"},
            {"phase": "done", "name": "產出報告", "agent": "technical-writer",
             "description": "彙整發現、建議下一步、產出研究報告"},
        ],
    },
}


def register_tools(mcp):
    """Register pipeline tools with the FastMCP instance."""

    @mcp.tool()
    async def pipeline_create(
        project_id: str,
        pipeline_type: str,
        idea_id: str = "",
    ) -> dict:
        """Create a development pipeline from an idea.

        This generates a structured workflow with phases and assigns agents.
        Each phase produces specific tasks that appear on the task wall.

        Args:
            project_id: The project UUID
            pipeline_type: Type of pipeline:
                - "embedded-firmware": MCU/RTOS firmware (M5Stack, ESP32, STM32)
                - "embedded-linux": Buildroot/Yocto, kernel drivers
                - "web-fullstack": React/FastAPI full-stack web app
                - "quick-prototype": Fast MVP to validate an idea
                - "research-spike": Technical investigation
            idea_id: Optional idea UUID to link this pipeline to
        """
        # Validate pipeline type
        valid_types = [t.value for t in PipelineType]
        if pipeline_type not in valid_types:
            return {"error": f"Unknown pipeline type: {pipeline_type}. Valid: {valid_types}"}

        template = PIPELINE_TEMPLATES.get(pipeline_type)
        if not template:
            return {"error": f"No template for pipeline type: {pipeline_type}"}

        # Create pipeline via API
        result = await _api_call("POST", "/api/pipelines/", json_data={
            "project_id": project_id,
            "pipeline_type": pipeline_type,
            "idea_id": idea_id,
        })

        # Now generate tasks for each phase
        tasks_created = []
        for i, phase in enumerate(template["phases"]):
            task = await _api_call("POST", "/api/tasks/", json_data={
                "project_id": project_id,
                "title": f"[{pipeline_type}] {phase['name']}",
                "description": phase["description"],
                "assigned_agent": phase["agent"],
                "priority": "high" if i == 0 else "medium",
            })
            tasks_created.append({
                "phase": phase["phase"],
                "task_id": task.get("id", ""),
                "title": phase["name"],
                "agent": phase["agent"],
            })

        return {
            "pipeline_id": result.get("id", ""),
            "pipeline_type": pipeline_type,
            "name": template["name"],
            "project_id": project_id,
            "phases": len(template["phases"]),
            "tasks_created": tasks_created,
            "current_phase": "idea",
            "message": (
                f"Pipeline '{template['name']}' created with {len(template['phases'])} phases. "
                f"{len(tasks_created)} tasks generated on the task wall. "
                f"Use pipeline_advance to move through phases."
            ),
        }

    @mcp.tool()
    async def pipeline_advance(pipeline_id: str) -> dict:
        """Advance the pipeline to the next phase.

        Marks the current phase as complete and activates the next phase.
        Related tasks on the task wall will be updated.

        Args:
            pipeline_id: The pipeline UUID from pipeline_create
        """
        return await _api_call("POST", f"/api/pipelines/{pipeline_id}/advance")

    @mcp.tool()
    async def pipeline_templates() -> dict:
        """List all available pipeline templates with their phases."""
        return {"templates": PIPELINE_TEMPLATES}

    @mcp.tool()
    async def pipeline_status(pipeline_id: str) -> dict:
        """Get the current status of a pipeline.

        Args:
            pipeline_id: The pipeline UUID
        """
        return await _api_call("GET", f"/api/pipelines/{pipeline_id}")
